from parselcli.prompt.runner import Prompter
from parselcli.render.memory import MemoryRenderer
from parsel import Selector


def _renderer(content: str, url="http://example.com"):
    r = MemoryRenderer()
    r.open()
    r.goto("http://example.com", content=content)
    return r


def test_Prompter():
    p = Prompter(_renderer("<h1>foobar</h1>"))
    assert p.select("h1::text")
    p.renderer.close()


def test_Prompter_parse_input():
    p = Prompter(_renderer("<h1>text</h1>"))
    result = p.parse_input("foo bar --help")
    assert result == ({"help": True}, "foo bar")

    result = p.parse_input("foo --help bar")
    assert result == ({"help": True}, "foo bar")

    assert p.parse_input("foo -s bar") == ({"strip": True}, "foo bar")

    assert p.parse_input("foo -1 bar") == ({"first": True}, "foo bar")
    assert p.parse_input("foo --first bar") == ({"first": True}, "foo bar")

    assert p.parse_input("foo --join bar") == ({"join": ""}, "foo bar")
    assert p.parse_input("foo --join-with , bar") == ({"join": ","}, "foo bar")

    assert p.parse_input("foo --join-with \n bar") == ({"join": "\n"}, "foo bar")


def test_Prompter_readline_cmd_switch():
    p = Prompter(_renderer("<h1>text</h1>"))
    # default is css selector
    assert p.completer is p._completer_css
    # --xpath/--css command should switch modes
    p.readline("--xpath")
    assert p.completer is p._completer_xpath
    p.readline("--css")
    assert p.completer is p._completer_css
    # switch and execute
    result, _ = p.readline("//h1/text() --xpath")
    assert p.completer is p._completer_xpath
    assert result == ["text"]


def test_Prompter_readline_newline_option_arg():
    p = Prompter(_renderer("<h1>text</h1><h1>text2</h1>"))
    result, _ = p.readline("//h1/text() --xpath --join-with \n")
    assert result == "text\ntext2"


def test_Prompter_readline_cmd_help(capfd):
    p = Prompter(_renderer("<h1>text</h1>"))
    result, _ = p.readline("--help")
    assert result is None
    # should print out commands and processors
    out = capfd.readouterr().err
    assert "Commands:" in out
    assert "Processors:" in out


def test_Prompter_readline_cmd_info(capfd):
    p = Prompter(_renderer("<h1>text</h1>"))
    result, _ = p.readline("--info")
    assert result is None
    # should print out commands and processors
    out = capfd.readouterr().err
    assert "Enabled processors:" in out
