import decimal
import pytest
from parselcli.processors import (
    AbsoluteUrl,
    First,
    FormatHtml,
    Len,
    Regex,
    Strip,
    Sum,
    Nth,
    Join,
    Collapse,
    Repr,
    Slice,
)


def test_Nth():
    proc = Nth(1)
    assert proc("1234") == ("2", {})
    assert proc(["1", "2", "3", "4"]) == ("2", {})
    with pytest.raises(IndexError):
        assert proc("1")
    with pytest.raises(TypeError):
        assert proc(True)
    proc = Nth(-1)
    assert proc("1234") == ("4", {})


def test_Join():
    proc = Join()
    assert proc("1234") == ("1234", {})
    assert proc(["1", "2", "3", "4"]) == ("1234", {})
    proc = Join(",")
    assert proc(["1", "2", "3", "4"]) == ("1,2,3,4", {})
    with pytest.raises(TypeError):
        assert proc(1234)


def test_Strip():
    proc = Strip()
    assert proc(" 1 \n") == ("1", {})
    assert proc([" 1 \n", "2.."]) == (["1", "2.."], {})
    proc = Strip(".,")
    assert proc([" 1 \n", "2.."]) == ([" 1 \n", "2"], {})


def test_Collapse():
    proc = Collapse()
    assert proc(["1"]) == ("1", {})
    assert proc(["1", "2"]) == (["1", "2"], {})


def test_First():
    proc = First()
    assert proc(["1"]) == ("1", {})
    assert proc(["1", "2"]) == ("1", {})


def test_AbsoluteUrl():
    base = "http://httpbin.org/"
    proc = AbsoluteUrl(base=base)
    assert proc("foo/bar") == (f"{base}foo/bar", {})
    assert proc(["foo/bar", "gaz/har"]) == ([f"{base}foo/bar", f"{base}gaz/har"], {})


def test_Len():
    proc = Len()
    assert proc("1234") == ("4", {})
    assert proc(["1234", "5678"]) == ("2", {})


def test_Repr():
    proc = Repr()
    assert proc(4.2) == ("4.2", {})
    assert proc([4.1, 4.2]) == ("[4.1, 4.2]", {})


def test_Regex():
    proc = Regex(r"\w \d+")
    assert proc("i 402") == ("i 402", {})
    assert proc(["i 402", "a 2"]) == (["i 402", "a 2"], {})
    assert proc("a i 402 file") == ("a i 402 file", {})
    assert proc("a i 402 file") == ("a i 402 file", {})

    proc = Regex(r"\w (\d+)")
    assert proc("i 402") == ("402", {})
    assert proc(["i 402", "a 2"]) == (["402", "2"], {})

    proc = Regex(r"(\w) (\d)")
    assert proc("i 402") == (["i", "4"], {})


def test_Slice():
    proc = Slice("1:3")
    assert proc(["1", "2", "3", "4"]) == (["2", "3"], {})
    assert proc("1234") == ("23", {})


def test_FormatHtml():
    proc = FormatHtml()
    assert proc("<div><a><b>foo</b></a></div>") == ("<div>\n <a>\n  <b>\n   foo\n  </b>\n </a>\n</div>", {})
    assert proc(["<div><a><b>foo</b></a></div>"]) == (["<div>\n <a>\n  <b>\n   foo\n  </b>\n </a>\n</div>"], {})


def test_Sum():
    proc = Sum()
    assert proc(["1", "2", "3"]) == ("6", {})
    assert proc(["1.1", "2.2", "3.3"]) == ("6.6", {})
    assert proc(["1.1", "2.2", "3", "0.3"]) == ("6.6", {})
    assert proc("1") == ("1", {})
    assert proc("1.666") == ("1.666", {})
    with pytest.raises(decimal.InvalidOperation):
        assert proc(["a", "b"])
