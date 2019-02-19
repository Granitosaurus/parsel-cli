import os
import pathlib
import shlex
import webbrowser
from collections import OrderedDict

import re
from inspect import signature

import click
import requests
from click import echo, BadOptionUsage, NoSuchOption
from parsel import Selector
from prompt_toolkit import prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from requests import Response

from parselcli.app import HISTORY
from parselcli.completer import MiddleWordCompleter
from parselcli.embed import embed_auto
from parselcli.parsing import InputOptionParser
from parselcli.processors import Strip, First, UrlJoin, Join, Collapse
from parselcli.completer import XPATH_COMPLETION, CSS_COMPLETION, BASE_COMPLETION

HELP = {
    'absolute': 'convert relative urls to absolute',
    'debug': 'show debug info',
    'embed': 'start interactive python shell',
    'fetch': 'download from new url',
    'first': "take first element when there's only one",
    'help': 'show help',
    'join': 'join results into one',
    'collapse': 'collapse lists when only 1 element',
    'strip': 'strip every element of trailing and leading spaces',
    'view': 'open current file in browser tab',
    'css': 'switch to css selectors',
    'xpath': 'switch to xpath selectors',
}


def find_attributes(sel, attr):
    """
    finds node attributes in a selector
    returns list of unique strings
    """
    classes = sel.xpath('//*/@{}'.format(attr)).extract()
    classes = [c.strip() for cs in classes for c in cs.split()]
    return list(set(classes))


def find_nodes(sel):
    """
    Finds node names in a selector
    :returns list of unique strings
    """
    nodes = sel.xpath('//*')
    nodes = [n.xpath('name()').extract_first() for n in nodes]
    return list(set(nodes))


def get_css_completion(sel):
    """generates completion items for css from a selector"""
    node_names = find_nodes(sel)
    classes = ['.' + c for c in find_attributes(sel, 'class')]
    ids = ['#' + c for c in find_attributes(sel, 'id')]
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
            preferred_embed_shell=None,
            start_in_css=False,
            flags=('collapse',)):
        """
        :param selector:
        :param response:
        :param preferred_embed_shell: which embeded python system should be preferred, see embed.PYTHON_SHELLS
        :param start_in_css: whether to start in css mode instead of xpath
        :param flags: default flags to enable
        """
        self.sel = selector
        self.response = response
        self.processors = []
        self.preferred_embed = preferred_embed_shell

        # setup completers
        self._create_completers(self.sel)
        self.completer = self.completer_xpath
        if start_in_css:
            self.completer = self.completer_css

        # setup interpreter flags and commands
        flags = flags or []
        for flag in flags:
            self.enable_flag(flag)
        # self.commands = self._get_commands()
        self._option_parser = None
        self._flags = None
        self._commands = None

    @classmethod
    def from_response(cls, response, preferred_embed_shell=None, start_in_css=False, flags=None):
        return cls(
            Selector(response.text),
            response=response,
            preferred_embed_shell=preferred_embed_shell,
            start_in_css=start_in_css,
            flags=flags)

    @classmethod
    def from_file(cls, file, *args, **kwargs):
        response = Response()
        response._content = file.read().encode('utf8')
        response.status_code = 200
        response.url = pathlib.Path(os.path.abspath(file.name)).as_uri()
        return cls(Selector(response.text), response=response, *args, **kwargs)

    def _create_completers(self, selector):
        """Initiated auto completers based on current selector"""
        self.completer_xpath = MiddleWordCompleter(
            BASE_COMPLETION + get_xpath_completion(selector), ignore_case=True,
            match_end=True,
            sentence=True,
        )
        self.completer_css = MiddleWordCompleter(
            BASE_COMPLETION + get_css_completion(selector), ignore_case=True,
            match_end=True,
            sentence=True,
        )

    @property
    def commands(self):
        if not self._commands:
            self._commands = {
                'help': self.cmd_help,
                'debug': self.cmd_debug,
                'embed': self.cmd_embed,
                'view': self.cmd_view,
                'fetch': self.cmd_fetch,
                'css': self.cmd_switch_to_css,
                'xpath': self.cmd_switch_to_xpath,
            }
        return self._commands

    @property
    def flags(self):
        if not self._flags:
            self._flags = dict()
            self._flags['strip'] = Strip()
            self._flags['first'] = First()
            self._flags['collapse'] = Collapse()
            self._flags['absolute'] = UrlJoin(self.response.url)
            self._flags['join'] = Join()
        return self._flags

    @property
    def option_parser(self):
        if not self._option_parser:
            opt = InputOptionParser()
            for k, v in self.commands.items():
                nargs = len(signature(v).parameters)
                opt.add_option('-' + k, nargs=nargs)
            for k, v in self.flags.items():
                nargs = len(signature(v).parameters) - 1
                opt.add_option('+-' + k, nargs=nargs)
            self._option_parser = opt
        return self._option_parser

    def cmd_fetch(self, text):
        url = text.strip()
        print('downloading {}'.format(url))
        self.response = requests.get(url)
        self.sel = Selector(text=self.response.text)
        self._create_completers(self.sel)

    def cmd_view(self):
        webbrowser.open_new_tab(self.response.url)

    def cmd_help(self):
        print('available commands (use -command):')
        for k, v in self.commands.items():
            print('  {}: {}'.format(k, HELP[k]))
        print('available flags (use +flag to enable and -flag to disable)')
        for k, v in self.flags.items():
            print('  {}: {}'.format(k, HELP[k]))

    def cmd_debug(self):
        print('{}-{}'.format(self.response.status_code, self.response.url))
        print('enabled processors:')
        for p in self.processors:
            print('  ' + type(p).__name__)

    def cmd_embed(self):
        namespace = {
            'sel': self.sel,
            'response': self.response,
            'request': self.response.request if self.response else None}
        embed_auto(namespace, preferred=self.preferred_embed)

    def enable_flag(self, flag):
        print('enabled flag: {}'.format(flag))
        item = self.flags[flag]
        if item in self.processors:
            self.disable_flag(flag)
            self.processors.append(item)
        else:
            self.processors.append(item)

    def disable_flag(self, flag):
        disable = self.flags[flag]
        past = len(self.processors)
        self.processors = [p for p in self.processors if not isinstance(p, type(disable))]
        if past > len(self.processors):
            print('disabled flag: {}'.format(flag))

    def process(self, data):
        """Process data through enabled flag processors"""
        try:
            for processor in self.processors:
                data = processor(data)
        except Exception as e:
            print(e)
        return data

    def get_xpath(self, text):
        """Tries to extract xpath from a selector"""
        try:
            return self.process(self.sel.xpath(text).extract())
        except Exception as f:
            echo('E: {}'.format(f))
            return self.process([])

    def get_css(self, text):
        """Tries to extract css from a selector"""
        try:
            return self.process(self.sel.css(text).extract())
        except Exception as f:
            echo('E: {}'.format(f))
            return self.process([])

    def parse_commands(self, text):
        cmds = shlex.split(text)
        try:
            parsed = self.option_parser.parse_args(cmds)[0].items()
        except (BadOptionUsage, NoSuchOption) as e:
            print(e)
            parsed = []
        for k, v in parsed:
            if not isinstance(v, (list, tuple)):
                v = [v]
            notation, k = [x for x in re.split('([+-])', k) if x]
            if k in self.commands:
                self.commands[k](*v)
                continue
            if k in self.flags:
                if notation == '+':
                    self.enable_flag(k)
                else:
                    self.disable_flag(k)

    def cmd_switch_to_css(self):
        print('switched to css')
        self.completer = self.completer_css

    def cmd_switch_to_xpath(self):
        print('switched to xpath')
        self.completer = self.completer_xpath

    def loop_prompt(self, start_in_embed=False):
        """main loop prompt"""
        prompt_history = FileHistory(HISTORY)
        while True:
            if start_in_embed:
                self.cmd_embed()
                start_in_embed = False
            text = prompt('> ', history=prompt_history,
                          auto_suggest=AutoSuggestFromHistory(),
                          enable_history_search=True,
                          completer=self.completer)
            if not text:
                continue
            # check flags and commands
            if re.match(r'[+-]\w+', text):
                self.parse_commands(text)
                continue
            if text == 'e':
                self.cmd_embed()
            if self.completer is self.completer_css:
                value = self.get_css(text)
            else:
                value = self.get_xpath(text)
            value_len = len(''.join(value))
            if value_len < 1000:
                echo(value)
            else:
                if click.confirm(f'very big output {value_len}, print?'):
                    echo(value)
