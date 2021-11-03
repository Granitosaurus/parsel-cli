""" Contains main flow tool for parselcli and related helper functions """
import os
import pathlib
import re
import shlex
import webbrowser
from functools import partial
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Dict, List, Optional, Tuple

import click
import requests
from click import BadOptionUsage, NoSuchOption, Option, OptionParser, echo
from loguru import logger as log
from parsel import Selector
from prompt_toolkit import HTML, prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import SimpleLexer
from requests import Response
from rich.console import Console

from parselcli.completer import CSS_COMPLETION, XPATH_COMPLETION, MiddleWordCompleter
from parselcli.embed import embed_auto
from parselcli.processors import (
    AbsoluteUrl,
    Collapse,
    First,
    FormatHtml,
    Join,
    Len,
    Nth,
    Processor,
    Slice,
    Strip,
    Repr,
    Regex,
    Sum,
)

echo = partial(echo, err=True)


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
        color=True,
        vi_mode=False,
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
        self.color = color
        self.vi_mode = vi_mode
        self.console = Console(soft_wrap=True, highlight=self.color, markup=True)
        self.raw_output = False
        self.pretty_output = True

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

        self.processors = {
            "strip": Strip,
            "collapse": Collapse,
            "absolute": partial(AbsoluteUrl, self.response.url if self.response else ""),
            "join": Join,
            "first": First,
            "n": Nth,
            "len": Len,
            "pretty": FormatHtml,
            "repr": Repr,
            "re": Regex,
            "slice": Slice,
            "sum": Sum,
        }
        self.option_parser = OptionParser()
        self.options_commands = [
            Option(["--help"], is_flag=True, help="print help"),
            Option(["--reset"], is_flag=True, help="reset session processors"),
            Option(["--embed"], is_flag=True, help="embed repl"),
            Option(["--info"], is_flag=True, help="show context info"),
            Option(["--css"], is_flag=True, help="switch to css input"),
            Option(["--xpath"], is_flag=True, help="switch to xpath input"),
            Option(["--open"], is_flag=True, help="open current url in web browser"),
            Option(["--view"], is_flag=True, help="open current doc in web browser"),
            Option(["--vi"], is_flag=True, help="toggle input to/from vi mode"),
            Option(["--fetch"], help="request new url"),
        ]
        self.options_processors = [
            Option(["--first", "-1"], is_flag=True, help="take only 1st value"),
            Option(["--pretty", "-p"], is_flag=True, help="pretty format html"),
            Option(["--slice", "-["], help="take slice"),
            Option(["--re"], help="filter values by regex or if capture groups are present return them"),
            Option(["--repr", "-r"], is_flag=True, help="represent output (e.g. show newline chars)"),
            Option(["--len", "-l"], is_flag=True, help="return total length"),
            Option(["--sum"], is_flag=True, help="sum all results"),
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
                flag_value="",
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

        # setup completers
        self._create_completers(self.sel)
        self.completer = self.completer_xpath
        if start_in_css:
            self.completer = self.completer_css
        self.output_history = []

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
        color=True,
        vi_mode=False,
    ):
        """create prompter with response object"""
        if "br" in response.headers.get("Content-Encoding", ""):
            # text = brotli.decompress(response.content).decode(response.encoding)
            text = response.text
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
            color=color,
            vi_mode=vi_mode,
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
        color=True,
        vi_mode=False,
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
            color=color,
            vi_mode=vi_mode,
        )

    def _create_completers(self, selector: Selector):
        """Initiated auto completers based on current selector"""
        base = [
            *self.option_parser._long_opt.keys(),  # pylint: disable=protected-access
            *self.option_parser._short_opt.keys(),  # pylint: disable=protected-access
        ]
        self.completer_xpath = MiddleWordCompleter(
            base + get_xpath_completion(selector),
            ignore_case=True,
            match_end=True,
            sentence=True,
        )
        self.completer_css = MiddleWordCompleter(
            base + get_css_completion(selector),
            ignore_case=True,
            match_end=True,
            sentence=True,
        )

    @property
    def commands(self) -> Dict[str, Callable]:
        """commands prompter support"""
        return {name.split("cmd_")[1]: getattr(self, name) for name in dir(self) if name.startswith("cmd_")}

    @property
    def bottom_toolbar(self):
        """generate prompt toolkit bottom toolbar HTML."""
        toolbar = "[vi]" if self.vi_mode else ""
        if self.response is not None:
            url = self.response.url
            if len(url) > 70:
                url = url[:67] + "..."
            cached = "cached" if getattr(self.response, "from_cache", None) else "live"
            toolbar += f" [{cached}] {self.response.status_code} {url}"
        toolbar += f" | {self.active_processors}"
        return HTML(toolbar)

    @property
    def rprompt(self):
        """generate prompt toolkit right prompt"""
        return "CSS" if self.completer is self.completer_css else "XPATH"

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
        if self.response is None:
            echo("No response object attached")
        else:
            echo(f"{self.response.status_code} {self.response.url}")
        echo(f"Enabled processors: {self.active_processors}")

    def cmd_embed(self):
        """Open current shell in embed repl"""
        request = self.response.request if self.response is not None else None
        namespace = {
            "sel": self.sel,
            "response": self.response,
            "resp": self.response,
            "request": request,
            "req": request,
            "outs": self.output_history,
            "out": self.output_history[-1] if self.output_history else None,
            "in_css": list(self.history_file_css.load_history_strings()),
            "in_xpath": list(self.history_file_xpath.load_history_strings()),
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
        self.active_processors = []
        echo(f"active processors: {self.active_processors}")

    def cmd_vi(self):
        """toggles vi mode of input"""
        self.vi_mode = not self.vi_mode
        echo(f"vi mode turned {'ON' if self.vi_mode else 'OFF'}")

    def process_data(self, data, processors=None) -> Tuple[Any, Dict]:
        """Process data through enabled flag processors."""
        if processors is None:
            processors = self.active_processors
        try:
            meta = {}
            for processor in processors:
                data, _meta = processor(data)
                meta.update(_meta)
        except Exception as exc:  # pylint: disable=W0703
            echo(f'processor "{processor}" failed: {exc}')
            log.exception("processor failed")
        return data, meta

    def get_xpath(self, text, processors: Optional[List[Processor]] = None) -> Tuple[Any, Dict]:
        """Try to extract xpath from a selector."""
        try:
            return self.process_data(self.sel.xpath(text).extract(), processors=processors)
        except Exception as exc:  # pylint: disable=W0703
            echo(f'E:"{text}": {exc}')
            return self.process_data([], processors=processors)

    def get_css(self, text, processors: Optional[List[Processor]] = None) -> Tuple[Any, Dict]:
        """Try to extract css from a selector."""
        try:
            return self.process_data(self.sel.css(text).extract(), processors=processors)
        except Exception as exc:  # pylint: disable=W0703
            echo(f'E:"{text}": {exc}')
            return self.process_data([], processors=processors)

    def parse_input(self, text: str):
        """Parse commands and flags from a string."""
        lex = shlex.shlex(text, posix=True)
        lex.whitespace = " "  # we want to keep newline chars etc
        lex.whitespace_split = True
        parsed, remainder, _ = self.option_parser.parse_args(list(lex))
        remainder = " ".join(remainder).strip()
        return parsed, remainder

    def loop_prompt(self, start_in_embed=False):
        """Run prompt loop that keeps reading input line and showing output until exit."""
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
                bottom_toolbar=self.bottom_toolbar,
                rprompt=self.rprompt,
                vi_mode=self.vi_mode,
            )
            text = text.replace("\\n", "\n")
            log.debug(f"got line input: {text!r}")
            if text.lower().strip() == "exit":
                return
            if text.lower().strip() == "help":
                self.cmd_help()
                continue
            if not text:
                continue
            result, meta = self.readline(text)
            log.debug(f"processed line input to: {result!r} with meta {meta!r}")
            try:
                value_len = len("".join(result))
                if self.warn_limit and value_len > self.warn_limit:
                    if not click.confirm(f"warning: long output ({value_len} characters), print?"):
                        continue
            except TypeError:
                pass
            self.console.print("" if result is None else result)
            if result:
                self.output_history.append(result)

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
        if re.search(r"-[\w\[]+", text):
            log.debug("line has -- options - extracting details")
            try:
                opts, remainder = self.parse_input(text)
            except (BadOptionUsage, NoSuchOption) as exc:
                echo(exc)
                return None, {}
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
            elif _inline_processors:
                log.debug(f"session processors changed: {processors}")
                self.active_processors = processors
                echo(f"active processors: {self.active_processors}")
                return None, {}
            # no processors and no remainder -> single command run
            else:
                return None, {}

        if self.completer is self.completer_css:
            log.info(f'extracting css "{text}" with processors: {processors}')
            value, meta = self.get_css(text, processors=processors)
        else:
            log.info(f'extracting xpath "{text}" with processors: {processors}')
            value, meta = self.get_xpath(text, processors=processors)
        return value, meta
