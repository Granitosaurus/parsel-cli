from functools import partial
import os
import pathlib
import shlex
import webbrowser

import re
from collections import OrderedDict
from inspect import signature
from tempfile import NamedTemporaryFile
from typing import List

import brotli
import click
import requests
from click import Option, OptionParser, echo, BadOptionUsage, NoSuchOption, Tuple
from parsel import Selector
from prompt_toolkit import prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import SimpleLexer
from requests import Response

from parselcli.completer import MiddleWordCompleter
from parselcli.embed import embed_auto
from parselcli.processors import Nth, Strip, First, AbsoluteUrl, Join, Collapse, Len
from parselcli.completer import XPATH_COMPLETION, CSS_COMPLETION, BASE_COMPLETION

HELP = {
    "absolute": "convert relative urls to absolute",
    "debug": "show debug info",
    "embed": "start interactive python shell",
    "fetch": "download from new url",
    "first": "take first element when there's only one",
    "help": "show help",
    "join": "join results into one",
    "len": "return length of results",
    "collapse": "collapse lists when only 1 element",
    "strip": "strip every element of trailing and leading spaces",
    "open": "open current url in browser tab",
    "view": "open current html in browser tab",
    "css": "switch to css selectors",
    "xpath": "switch to xpath selectors",
}


def find_attributes(sel, attr):
    """
    finds node attributes in a selector
    returns list of unique strings
    """
    classes = sel.xpath("//*/@{}".format(attr)).extract()
    classes = [c.strip() for cs in classes for c in cs.split()]
    return list(set(classes))


def find_nodes(sel):
    """
    Finds node names in a selector
    :returns list of unique strings
    """
    nodes = sel.xpath("//*")
    nodes = [n.xpath("name()").extract_first() for n in nodes]
    return list(set(nodes))


def get_css_completion(sel):
    """generates completion items for css from a selector"""
    node_names = find_nodes(sel)
    classes = ["." + c for c in find_attributes(sel, "class")]
    ids = ["#" + c for c in find_attributes(sel, "id")]
    return node_names + classes + ids + CSS_COMPLETION


def get_xpath_completion(sel):
    """generates completion items for xpath from a selector"""
    completion = find_nodes(sel)
    return completion + XPATH_COMPLETION


class Prompter:
    """
    Prompt Toolkit container for all interpreter functions
    """

    def __init__(
        self,
        selector: Selector,
        response: Response = None,
        preferred_embed_shell: str = None,
        start_in_css=False,
        history_file_css=None,
        history_file_xpath=None,
        history_file_embed=None,
    ):
        """
        :param selector:
        :param response:
        :param preferred_embed_shell: which embeded python system should be preferred, see embed.PYTHON_SHELLS
        :param start_in_css: whether to start in css mode instead of xpath
        :param flags: default flags to enable
        """
        self._option_parser = None
        self._flags = None
        self._commands = None

        self.history_file_css = FileHistory(history_file_css)
        self.history_file_xpath = FileHistory(history_file_xpath)
        self.history_file_embed = history_file_embed
        if start_in_css:
            self.prompt_history = self.history_file_css
        else:
            self.prompt_history = self.history_file_xpath
        self.sel = selector
        self.response = response
        self.active_processors = []
        self.preferred_embed = preferred_embed_shell

        # setup completers
        self._create_completers(self.sel)
        self.completer = self.completer_xpath
        if start_in_css:
            self.completer = self.completer_css

        self.processors = {
            "strip": Strip,
            "collapse": Collapse,
            "absolute": partial(AbsoluteUrl, self.response.url if self.response else ""),
            "join": Join,
            "first": First,
            "n": Nth,
            "len": Len,
        }
        self.option_parser = OptionParser()
        self.options_commands = [
            Option(["--help"], is_flag=True, help="print help"),
            Option(["--embed"], is_flag=True, help="embed repl"),
            Option(["--info"], is_flag=True, help="show context info"),
            Option(["--css"], is_flag=True, help="switch to css input"),
            Option(["--xpath"], is_flag=True, help="siwtch to xpath input"),
            Option(["--open"], is_flag=True, help="open current url in web browser"),
            Option(["--view"], is_flag=True, help="open current doc in web browser"),
        ]
        self.options_processors = [
            Option(["--first", "-1"], is_flag=True, help="take only 1st value"),
            Option(["--len", "-l"], is_flag=True, help="return total length"),
            Option(
                ["--strip", "-s"],
                is_flag=True,
                help="strip away trailing chars",
            ),
            Option(
                ["--absolute", "-a"],
                is_flag=True,
                help="turn relative urls to absolute ones",
            ),
            Option(
                ["--collapse", "-c"],
                is_flag=True,
                help="collapse single element lists",
            ),
            Option(
                ["--join", "-j", "join"],
                is_flag=True,
                flag_value=" ",
                help="join results",
            ),
            Option(
                ["--join-with", "-J", "join"],
                help="join results with specified character",
            ),
            Option(
                ['-n'], help="take n-th element", type=click.INT
            )
        ]
        for opt in self.options_commands + self.options_processors:
            opt.add_to_parser(self.option_parser, None)

    @classmethod
    def from_response(
        cls,
        response,
        preferred_embed_shell=None,
        start_in_css=False,
        flags=None,
        history_file_css=None,
        history_file_xpath=None,
        history_file_embed=None,
    ):
        if "br" in response.headers.get("Content-Encoding", ""):
            text = brotli.decompress(response.content).decode(response.encoding)
        else:
            text = response.text
        return cls(
            Selector(text),
            response=response,
            preferred_embed_shell=preferred_embed_shell,
            start_in_css=start_in_css,
            history_file_css=history_file_css,
            history_file_xpath=history_file_xpath,
            history_file_embed=history_file_embed,
        )

    @classmethod
    def from_file(
        cls,
        file,
        preferred_embed_shell=None,
        start_in_css=False,
        flags=None,
        history_file_css=None,
        history_file_xpath=None,
        history_file_embed=None,
    ):
        response = Response()
        response._content = file.read().encode("utf8")
        response.status_code = 200
        response.url = pathlib.Path(os.path.abspath(file.name)).as_uri()
        return cls(
            Selector(response.text),
            response=response,
            preferred_embed_shell=preferred_embed_shell,
            start_in_css=start_in_css,
            history_file_css=history_file_css,
            history_file_xpath=history_file_xpath,
            history_file_embed=history_file_embed,
        )

    def _create_completers(self, selector):
        """Initiated auto completers based on current selector"""
        self.completer_xpath = MiddleWordCompleter(
            BASE_COMPLETION + get_xpath_completion(selector),
            ignore_case=True,
            match_end=True,
            sentence=True,
        )
        self.completer_css = MiddleWordCompleter(
            BASE_COMPLETION + get_css_completion(selector),
            ignore_case=True,
            match_end=True,
            sentence=True,
        )

    @property
    def commands(self):
        return {
            name.split("cmd_")[1]: getattr(self, name)
            for name in dir(self)
            if name.startswith("cmd_")
        }

    def cmd_fetch(self, text):
        url = text.strip()
        print("downloading {}".format(url))
        self.response = requests.get(url)
        self.sel = Selector(text=self.response.text)
        self._create_completers(self.sel)

    def cmd_open(self):
        webbrowser.open_new_tab(self.response.url)

    def cmd_view(self):
        with NamedTemporaryFile(
            "w", encoding=self.response.encoding, delete=False, suffix=".html"
        ) as file:
            file.write(self.response.text)
        webbrowser.open_new_tab(f"file://{file.name}")

    def cmd_help(self):
        print("Commands:")
        for opt in self.options_commands:
            print(f"{', '.join(opt.opts + opt.secondary_opts):<25}{opt.help}")
        print("Processors:")
        for opt in self.options_processors:
            print(f"{', '.join(opt.opts + opt.secondary_opts):<25}{opt.help}")

    def cmd_info(self):
        print("{}-{}".format(self.response.status_code, self.response.url))
        print("enabled processors:")
        for p in self.active_processors:
            print("  " + type(p).__name__)

    def cmd_embed(self):
        namespace = {
            "sel": self.sel,
            "response": self.response,
            "request": self.response.request if self.response else None,
        }
        embed_auto(
            namespace,
            preferred=self.preferred_embed,
            history_filename=self.history_file_embed,
        )

    def cmd_css(self):
        print("switched to css")
        self.completer = self.completer_css
        self.prompt_history = self.history_file_css

    def cmd_xpath(self):
        print("switched to xpath")
        self.completer = self.completer_xpath
        self.prompt_history = self.history_file_xpath

    def process_data(self, data, processors=None):
        """Process data through enabled flag processors"""
        if processors is None:
            processors = self.active_processors
        try:
            for processor in processors:
                data = processor(data)
        except Exception as e:
            print(e)
        return data

    def get_xpath(self, text, processors=None):
        """Tries to extract xpath from a selector"""
        try:
            return self.process_data(
                self.sel.xpath(text).extract(), processors=processors
            )
        except Exception as f:
            echo(f'E:"{text}": {f}')
            return self.process_data([], processors=processors)

    def get_css(self, text, processors=None):
        """Tries to extract css from a selector"""
        try:
            return self.process_data(
                self.sel.css(text).extract(), processors=processors
            )
        except Exception as f:
            echo(f'E:"{text}": {f}')
            return self.process_data([], processors=processors)

    def parse_input(self, text: str):
        """
        Parses commands and flags from a string
        :returns remaining_text, found_commands, found_flags_to_enable, found_flags_to_disable
        """
        lex = shlex.shlex(text, posix=True)
        lex.whitespace = " "  # we want to keep newline chars etc
        lex.whitespace_split = True
        parsed, remainder, _ = self.option_parser.parse_args(list(lex))
        remainder = ' '.join(remainder).strip()
        return parsed, remainder

    def loop_prompt(self, start_in_embed=False):
        """main loop prompt"""
        while True:
            if start_in_embed:
                self.cmd_embed()
                start_in_embed = False
            text = prompt(
                "> ",
                history=self.prompt_history,
                auto_suggest=AutoSuggestFromHistory(),
                enable_history_search=True,
                completer=self.completer,
                lexer=SimpleLexer()
            )
            text = text.replace('\\n', '\n')
            if not text:
                continue
            processors = self.active_processors
            # check flags and commands
            if re.search(r"[+-]\w+", text):
                try:
                    opts, remainder = self.parse_input(text)
                except (BadOptionUsage, NoSuchOption) as e:
                    echo(e)
                    continue
                # if any commands are found execute first one
                _inline_processors = []
                for name, value in opts.items():
                    if name in self.commands:
                        if value is True:
                            self.commands[name]()
                        else:
                            self.commands[name](value)
                    elif name in self.processors:
                        if value is True:
                            _inline_processors.append(self.processors[name]())
                        else:
                            _inline_processors.append(self.processors[name](value))

                # enable temporary processors
                if _inline_processors:
                    processors = _inline_processors
                if remainder:
                    text = remainder.strip("'")
                else:
                    self.active_processors = processors
                    echo(f"default processors: {self.active_processors}")
                    continue

            if self.completer is self.completer_css:
                value = self.get_css(text, processors=processors)
            else:
                value = self.get_xpath(text, processors=processors)
            try:
                value_len = len("".join(value))
                if value_len < 2000:
                    echo(value)
                else:
                    if click.confirm(f"very big output {value_len}, print?"):
                        echo(value)
            except TypeError:
                echo(value)
