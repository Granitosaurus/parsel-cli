"""
Contains main flow tool for parselcli and related helper functions
"""
import os
import pathlib
import re
import shlex
import webbrowser
from functools import partial
from tempfile import NamedTemporaryFile
from typing import Callable, Dict

import brotli
import click
import requests
from click import BadOptionUsage, NoSuchOption, Option, OptionParser, echo
from parsel import Selector
from prompt_toolkit import prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import SimpleLexer
from requests import Response
from loguru import logger as log

from parselcli.completer import (
    BASE_COMPLETION,
    CSS_COMPLETION,
    XPATH_COMPLETION,
    MiddleWordCompleter,
)
from parselcli.embed import embed_auto
from parselcli.processors import AbsoluteUrl, Collapse, First, Join, Len, Nth, Strip


def find_attributes(sel, attr):
    """
    finds node attributes in a selector
    returns list of unique strings
    """
    classes = sel.xpath(f"//*/@{attr}").extract()
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
        start_in_css=True,
        history_file_css=None,
        history_file_xpath=None,
        history_file_embed=None,
        warn_limit=None,
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

        self.warn_limit = 2000 if warn_limit is None else warn_limit
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
            Option(["-n"], help="take n-th element", type=click.INT),
        ]
        for opt in self.options_commands + self.options_processors:
            opt.add_to_parser(self.option_parser, None)

    @classmethod
    def from_response(
        cls,
        response,
        preferred_embed_shell=None,
        start_in_css=True,
        history_file_css=None,
        history_file_xpath=None,
        history_file_embed=None,
        warn_limit=None,
    ):
        """create prompter with response object"""
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
            warn_limit=warn_limit,
        )

    @classmethod
    def from_file(
        cls,
        file,
        preferred_embed_shell=None,
        start_in_css=True,
        history_file_css=None,
        history_file_xpath=None,
        history_file_embed=None,
        warn_limit=None,
    ):
        """create prompter from html file"""
        response = Response()
        response._content = file.read().encode("utf8")  # pylint: disable=W0212
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
            warn_limit=warn_limit,
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
    def commands(self) -> Dict[str, Callable]:
        """commands prompter support"""
        return {name.split("cmd_")[1]: getattr(self, name) for name in dir(self) if name.startswith("cmd_")}

    def cmd_fetch(self, text):
        """switch current session to different url by making a new request"""
        url = text.strip()
        echo(f"requesting: {url}")
        self.response = requests.get(url)
        self.sel = Selector(text=self.response.text)
        self._create_completers(self.sel)

    def cmd_open(self):
        """open current response url in browser"""
        webbrowser.open_new_tab(self.response.url)

    def cmd_view(self):
        """open current response data in browser"""
        with NamedTemporaryFile("w", encoding=self.response.encoding, delete=False, suffix=".html") as file:
            file.write(self.response.text)
        webbrowser.open_new_tab(f"file://{file.name}")

    def cmd_help(self):
        """print usage help"""
        echo("Commands:")
        for opt in self.options_commands:
            echo(f"{', '.join(opt.opts + opt.secondary_opts):<25}{opt.help}")
        echo("Processors:")
        for opt in self.options_processors:
            echo(f"{', '.join(opt.opts + opt.secondary_opts):<25}{opt.help}")

    def cmd_info(self):
        """print info about current session"""
        if self.response:
            echo(f"{self.response.status_code} {self.response.url}")
        else:
            echo("No response object attached")
        echo("enabled processors:")
        for processor in self.active_processors:
            echo("  " + type(processor).__name__)

    def cmd_embed(self):
        """Open current shell in embed repl"""
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
        """switch current session to css selectors"""
        echo("switched to css")
        self.completer = self.completer_css
        self.prompt_history = self.history_file_css

    def cmd_xpath(self):
        """switch current session to xpath selectors"""
        echo("switched to xpath")
        self.completer = self.completer_xpath
        self.prompt_history = self.history_file_xpath

    def cmd_reset(self):
        """resets current processors"""
        echo(f"default processors: {self.active_processors}")
        self.active_processors = []

    def process_data(self, data, processors=None):
        """Process data through enabled flag processors"""
        if processors is None:
            processors = self.active_processors
        try:
            for processor in processors:
                data = processor(data)
        except Exception as exc:  # pylint: disable=W0703
            echo(exc)
        return data

    def get_xpath(self, text, processors=None):
        """Tries to extract xpath from a selector"""
        try:
            return self.process_data(self.sel.xpath(text).extract(), processors=processors)
        except Exception as exc:  # pylint: disable=W0703
            echo(f'E:"{text}": {exc}')
            return self.process_data([], processors=processors)

    def get_css(self, text, processors=None):
        """Tries to extract css from a selector"""
        try:
            return self.process_data(self.sel.css(text).extract(), processors=processors)
        except Exception as exc:  # pylint: disable=W0703
            echo(f'E:"{text}": {exc}')
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
        remainder = " ".join(remainder).strip()
        return parsed, remainder

    def loop_prompt(self, start_in_embed=False):
        """
        main loop prompt that keeps reading input line until exit
        """
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
                lexer=SimpleLexer(),
            )
            text = text.replace("\\n", "\n")
            log.debug(f"got line input: {text!r}")
            if text.lower().strip() == "exit":
                return
            if not text:
                continue
            echo(self.readline(text))

    def readline(self, text: str) -> str:  # pylint: disable=R0912
        """
        read single input line and do one/many of following:
        - execute css or xpath expression
        - execute command
        - enable inline processor
        - enable session processor

        returns executed css/xpath
        """
        processors = self.active_processors
        # check flags and commands
        if re.search(r"-\w+", text):
            log.debug("line has -- options - extracting details")
            try:
                opts, remainder = self.parse_input(text)
            except (BadOptionUsage, NoSuchOption) as exc:
                echo(exc)
                return
            # if any commands are found execute first one
            _inline_processors = []
            for name, value in opts.items():
                if name in self.commands:
                    log.debug(f"found command {name!r}; executing")
                    if value is True:
                        self.commands[name]()
                    else:
                        self.commands[name](value)
                elif name in self.processors:
                    log.debug(f"found inline processor {name!r}")
                    if value is True:
                        _inline_processors.append(self.processors[name]())
                    else:
                        _inline_processors.append(self.processors[name](value))

            # enable temporary processors
            if _inline_processors:
                log.debug(f"using inline processors: {_inline_processors}")
                processors = _inline_processors
            # options with remaining text -> css or xpath is up for execution
            if remainder:
                log.debug(f"command has remainder selectors to execute: {remainder}")
                text = remainder.strip("'")
            # option with no text -> default processors were activated
            elif processors:
                log.debug(f"session processors changed: {processors}")
                self.active_processors = processors
                echo(f"default processors: {self.active_processors}")
                return
            # no processors and no remainder -> single command run
            else:
                return

        if self.completer is self.completer_css:
            log.info(f'extracting css "{text}" with processors: {processors}')
            value = self.get_css(text, processors=processors)
        else:
            log.info(f'extracting xpath "{text}" with processors: {processors}')
            value = self.get_xpath(text, processors=processors)
        try:
            value_len = len("".join(value))
            if self.warn_limit and value_len > self.warn_limit:
                if not click.confirm(f"very big output {value_len}, print?"):
                    return
        except TypeError:
            pass
        return value
