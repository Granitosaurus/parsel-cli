""" Contains main flow tool for parselcli and related helper functions """
import re
from shlex import shlex
from functools import partial
from typing import Any, List, Optional, Tuple, Dict

import click
from click import BadOptionUsage, NoSuchOption, Option, OptionParser, echo
from loguru import logger as log
from parsel import Selector
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import SimpleLexer
from rich.console import Console

from parselcli.prompt.completer import MiddleWordCompleter
from parselcli.prompt.utils import get_css_completion, get_xpath_completion
from parselcli.render import Renderer
from parselcli.prompt.commands import PromptCommands
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


class Prompter:
    """
    Prompt Toolkit container for all interpreter functions
    """

    processors = {
        "strip": Strip,
        "collapse": Collapse,
        "absolute": AbsoluteUrl,
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
    option_parser = OptionParser()
    options_commands = [
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
        Option(["--clipin"], is_flag=True, help="copy last input to clipboard"),
        Option(["--clipout"], is_flag=True, help="copy last output to clipboard"),
    ]
    options_processors = [
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
    for opt in options_commands + options_processors:
        opt.add_to_parser(option_parser, None)

    def __init__(
        self,
        renderer: Renderer,
        history_file_css=None,
        history_file_xpath=None,
        history_file_embed=None,
        start_in_css=True,
        color=True,
        vi_mode=False,
        preferred_embed=None,
    ):
        """
        :param renderer: TODO
        :param start_in_css: whether to start in css mode instead of xpath
        :param flags: default flags to enable
        """
        self._option_parser = None
        self._flags = None
        self._commands = None
        self._sel = None
        self._processors = None

        self.use_color = color
        self.use_vi_mode = vi_mode
        self.preferred_embed_shell = preferred_embed

        self.console = Console(soft_wrap=True, highlight=self.use_color, markup=True)
        self._history_file_css = FileHistory(history_file_css)
        self._history_file_xpath = FileHistory(history_file_xpath)
        self._history_file_embed = history_file_embed
        self.mode = "css" if start_in_css else "xpath"

        self.renderer = renderer
        self.active_processors = []
        self.cmd = PromptCommands(self)

        # setup completers
        self.create_completers(self.renderer.selector)
        self.output_history = []

    @property
    def prompt_history(self):
        if self.mode == "css":
            return self._history_file_css
        return self._history_file_xpath

    @property
    def completer(self):
        if self.mode == "css":
            return self._completer_css
        return self._completer_xpath

    def create_completers(self, selector: Selector):
        """Initiated auto completers based on current selector"""
        log.debug("creating completers based on current selector")
        base = [
            *self.option_parser._long_opt.keys(),  # pylint: disable=protected-access
            *self.option_parser._short_opt.keys(),  # pylint: disable=protected-access
        ]
        self._completer_xpath = MiddleWordCompleter(
            base + get_xpath_completion(selector) if selector else [],
            ignore_case=True,
            match_end=True,
            sentence=True,
        )
        self._completer_css = MiddleWordCompleter(
            base + get_css_completion(selector) if selector else [],
            ignore_case=True,
            match_end=True,
            sentence=True,
        )

    @property
    def bottom_toolbar(self):
        """generate prompt toolkit bottom toolbar HTML."""
        toolbar = "[vi]" if self.use_vi_mode else ""
        if self.renderer.response is not None:
            url = self.renderer.response.url
            if len(url) > 70:
                url = url[:67] + "..."
            cached = "cached" if getattr(self.renderer.response, "from_cache", None) else "live"
            toolbar += f" [{cached}] {self.renderer.response.status_code} {url}"
        toolbar += f" | {self.active_processors}"
        log.debug(f"generating toolbar from {toolbar}")
        return toolbar

    @property
    def rprompt(self):
        """generate prompt toolkit right prompt"""
        return "CSS" if self.completer is self._completer_css else "XPATH"

    @property
    def selector(self):
        """lazy selector; will initiate compelters on first call"""
        sel = self.renderer.selector
        self.create_completers(sel)
        return sel

    def process_data(self, data, processors=None) -> Tuple[Any, Dict]:
        """Process data through enabled flag processors."""
        if processors is None:
            processors = self.active_processors
        try:
            meta = {}
            for processor in processors:
                data, _meta = processor(data, response=self.renderer.response)
                meta.update(_meta)
        except Exception as exc:  # pylint: disable=W0703
            echo(f'processor "{processor}" failed: {exc}')
            log.exception("processor failed")
        return data, meta

    def _get_xpath(self, text, processors: Optional[List[Processor]] = None) -> Tuple[Any, Dict]:
        """Try to extract xpath from a selector."""
        try:
            return self.process_data(self.selector.xpath(text).extract(), processors=processors)
        except Exception as exc:  # pylint: disable=W0703
            echo(f'E:"{text}": {exc}')
            return self.process_data([], processors=processors)

    def _get_css(self, text, processors: Optional[List[Processor]] = None) -> Tuple[Any, Dict]:
        """Try to extract css from a selector."""
        try:
            return self.process_data(self.selector.css(text).extract(), processors=processors)
        except Exception as exc:  # pylint: disable=W0703
            echo(f'E:"{text}": {exc}')
            return self.process_data([], processors=processors)

    def select(self, selector, processors: Optional[List[Processor]] = None) -> Tuple[Any, Dict]:
        """try to extract css or xpath (based on current mode settings: self.mode)"""
        log.info(f'extracting {self.mode} "{selector}" with processors: {processors}')
        if self.mode == "css":
            return self._get_css(selector, processors)
        return self._get_xpath(selector, processors)

    def parse_input(self, text: str):
        """Parse commands and flags from a string."""

        def shlex_split(text):
            lex = shlex(text, posix=False)
            lex.whitespace_split = True
            lex.whitespace = " "  # we want to keep newline chars etc
            lex.commenters = ""  # disable comment parsing
            return list(lex)

        parsed, remainder, _ = self.option_parser.parse_args(shlex_split(text))
        remainder = " ".join(remainder).strip()
        log.debug(f'parsed input: "{text}" to "{parsed}" with remainder "{remainder}"')
        return parsed, remainder

    def loop_prompt(self, start_in_embed=False):
        """Run prompt loop that keeps reading input line and showing output until exit."""

        session: PromptSession[str] = PromptSession(
            history=self.prompt_history,
            auto_suggest=AutoSuggestFromHistory(),
            complete_in_thread=True,
            enable_history_search=True,
            lexer=SimpleLexer(),
            vi_mode=self.use_vi_mode,
            bottom_toolbar=self.bottom_toolbar,
            rprompt=self.rprompt,
            completer=self.completer,
        )
        while True:
            if start_in_embed:
                self.cmd.cmd_embed()
                start_in_embed = False
            # XXX: is this the only way to change history aside from initiating session in every loop?
            session.default_buffer.history = self.prompt_history
            text = session.prompt(
                "> ",
                in_thread=True,
                bottom_toolbar=self.bottom_toolbar,
                rprompt=self.rprompt,
                completer=self.completer,
            )
            text = text.replace("\\n", "\n")
            log.debug(f"got line input: {text!r}")
            if text.lower().strip() == "exit":
                return
            if text.lower().strip() == "help":
                self.cmd.cmd_help()
                continue
            if not text:
                continue
            result, meta = self.readline(text)
            log.debug(f"processed line input to: {result!r} with meta {meta!r}")
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
                log.error("failed to parse input")
                echo(exc)
                return None, {}
            # if any commands are found execute first one
            _inline_processors = []
            log.debug(f'parsed opts: "{opts}" and remainder: "{remainder}" from "{text}"')
            for name, value in opts.items():
                if name in self.cmd.commands:
                    log.debug(f"found command {name!r}; executing")
                    if value is True:
                        self.cmd.commands[name]()
                    else:
                        self.cmd.commands[name](value)
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
            if opts and remainder:
                log.debug(f"command has remainder selectors to execute: {remainder}")
                text = remainder.strip("'")
            # option with no text -> default processors were activated
            elif _inline_processors:
                log.debug(f"session processors changed: {processors}")
                self.active_processors = processors
                echo(f"active processors: {self.active_processors}")
                return None, {}
            # no processors and no remainder -> single command run
            elif not remainder:
                return None, {}
            # otherwise have remainder but no processors -> false positive, the whole string was just a selector
            else:
                pass

        return self.select(text, processors=processors)
