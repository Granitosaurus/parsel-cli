import os

from click import echo
from parsel import Selector
from prompt_toolkit import prompt, AbortAction
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory

from parselcli.completer import MiddleWordCompleter
from parselcli.embed import embed_auto
from parselcli.processors import Strip, First, UrlJoin

XPATH_FUNCTIONS = ['text()', 'contains(', 're:test(', 'following-sibling(', 'position()', 'last()']
CSS_FUNCTIONS = ['::text', '::attr(']
_FLAGS = ['strip', 'first', 'absolute', 'onlyfirst']
BASE_COMPLETION = ['css', 'xpath', '-help', '-debug']
for flag in _FLAGS:
    BASE_COMPLETION.extend(['+'+flag, '-'+flag])


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
    return node_names + classes + ids + CSS_FUNCTIONS


def get_xpath_completion(sel):
    """generates completion items for xpath from a selector"""
    completion = find_nodes(sel)
    return completion + XPATH_FUNCTIONS


class Prompter:
    """
    Prompt Toolkit container for all interpreter functions
    """

    def __init__(self, text, response=None, preferred_embed=None, start_in_css=False, flags=None):
        self.sel = Selector(text)
        self.response = response
        self.processors = []
        self.preferred_embed = preferred_embed
        # setup completers
        self.completer_xpath = MiddleWordCompleter(BASE_COMPLETION + get_xpath_completion(self.sel), ignore_case=True,
                                                   match_end=True,
                                                   sentence=True)
        self.completer_css = MiddleWordCompleter(BASE_COMPLETION + get_css_completion(self.sel), ignore_case=True,
                                                 match_end=True,
                                                 sentence=True)
        self.completer = self.completer_css if start_in_css else self.completer_xpath
        # setup interpreter flags and commands
        self.flags_processors = self._set_flags()
        for flag in flags:
            self._enable_flag(flag)
        self.commands = self._set_commands()

    def _set_commands(self):
        return {
            'help': self._print_help,
            'debug': self._print_debug,
            'embed': self._embed,
        }

    def _set_flags(self):
        return {
            'strip': Strip(),
            'first': First(),
            'onlyfirst': First(only=True),
            'absolute': UrlJoin(self.response.url)
        }

    def _print_help(self):
        print('available commands (use -command):')
        for c in self.commands:
            print('  ' + c)
        print('available flags (use +flag to enable and -flag to disable)')
        for c in self.flags_processors:
            print('  ' + c)

    def _print_debug(self):
        print('enabled processors:')
        for p in self.processors:
            print('  ' + type(p).__name__)

    def _embed(self):
        namespace = {
            'sel': self.sel,
            'response': self.response,
            'request': self.response.request if self.response else None}
        embed_auto(namespace, preferred=self.preferred_embed)

    def _enable_flag(self, flag):
        print('enabled flag: {}'.format(flag))
        self.processors.append(self.flags_processors[flag])

    def _disable_flag(self, flag):
        try:
            self.processors.remove(self.flags_processors[flag])
            print('disabled flag: {}'.format(flag))
        except ValueError:
            pass

    def process(self, data):
        for processor in self.processors:
            data = processor(data)
        return data

    def get_xpath(self, text):
        """Tries to extract xpath from a selector"""
        data = []
        try:
            data = self.sel.xpath(text).extract()
        except Exception as f:
            echo('E: {}'.format(f))
        return self.process(data)

    def get_css(self, text):
        """Tries to extract css from a selector"""
        try:
            return self.process(self.sel.css(text).extract())
        except Exception as f:
            echo('E: {}'.format(f))
            return []

    def _completer_xpath(self):
        print('switching to xpath')
        self.completer = self.completer_xpath

    def _completer_css(self):
        print('switching to css')
        self.completer = self.completer_css

    def start_prompt_mode(self, start_in_embed=False):
        prompt_history = FileHistory(os.path.expanduser('~/.parsel_history'))
        while True:
            if start_in_embed:
                self._embed()
                start_in_embed = False
            text = prompt('> ', history=prompt_history,
                          auto_suggest=AutoSuggestFromHistory(),
                          enable_history_search=True,
                          completer=self.completer,
                          on_abort=AbortAction.RETRY)
            if not text:
                continue
            # check flags and commands
            if text.startswith('+') or text.startswith('-'):
                notation, text = text[0], text[1:]
                if text in self.commands:
                    self.commands[text]()
                    continue
                if text in self.flags_processors:
                    if notation == '+':
                        self._enable_flag(text)
                    else:
                        self._disable_flag(text)
                    continue
            if text == 'css':
                self._completer_css()
                continue
            if text == 'xpath':
                self._completer_xpath()
                continue
            if self.completer is self.completer_css:
                echo(self.get_css(text))
            else:
                echo(self.get_xpath(text))