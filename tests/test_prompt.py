from parselcli.prompt import Prompter
from parsel import Selector


def test_Prompter():
    p = Prompter(Selector("<h1>text</h1>"))
    assert p


def test_Prompter_parse_input():
    p = Prompter(Selector("<h1>text</h1>"))
    result = p.parse_input("foo bar --help")
    assert result == ({"help": True}, "foo bar")

    result = p.parse_input("foo --help bar")
    assert result == ({"help": True}, "foo bar")

    assert p.parse_input("foo -s bar") == ({"strip": True}, "foo bar")

    assert p.parse_input("foo -1 bar") == ({"first": True}, "foo bar")
    assert p.parse_input("foo --first bar") == ({"first": True}, "foo bar")

    assert p.parse_input("foo --join bar") == ({"join": " "}, "foo bar")
    assert p.parse_input("foo --join-with , bar") == ({"join": ","}, "foo bar")

    assert p.parse_input("foo --join-with \n bar") == ({"join": "\n"}, "foo bar")


def test_Prompter_readline_cmd_switch():
    p = Prompter(Selector("<h1>text</h1>"))
    # default is css selector
    assert p.completer is p.completer_css
    # --xpath/--css command should switch modes
    p.readline("--xpath")
    assert p.completer is p.completer_xpath
    p.readline("--css")
    assert p.completer is p.completer_css
    # switch and execute
    result = p.readline("//h1/text() --xpath")
    assert p.completer is p.completer_xpath
    assert result == ["text"]

def test_Prompter_readline_newline_option_arg():
    p = Prompter(Selector("<h1>text</h1><h1>text2</h1>"))
    result = p.readline("//h1/text() --xpath --join-with \n")
    assert result == "text\ntext2"


def test_Prompter_readline_cmd_help(capfd):
    p = Prompter(Selector("<h1>text</h1>"))
    result = p.readline("--help")
    assert result is None
    # should print out commands and processors
    out = capfd.readouterr().out
    assert "Commands:" in out
    assert "Processors:" in out


def test_Prompter_readline_cmd_info(capfd):
    p = Prompter(Selector("<h1>text</h1>"))
    result = p.readline("--info")
    assert result is None
    # should print out commands and processors
    out = capfd.readouterr().out
    assert "enabled processors:" in out
