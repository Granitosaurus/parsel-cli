"""
Contains processor callables for parselcli
"""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup


class Processor:
    """Base class for parselcli processors"""

    def __repr__(self) -> str:
        return f"{type(self).__name__}"


class Nth(Processor):
    """Take nth element of a list"""

    def __init__(self, position: int) -> None:
        self.position = int(position)

    def __call__(self, values):
        return values[self.position], {}

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.position})"


class Join(Processor):
    """Join multiple values with separator"""

    def __init__(self, sep=""):
        self.sep = sep

    def __call__(self, values):
        return self.sep.join(values), {}

    def __repr__(self) -> str:
        return f"{type(self).__name__}({repr(self.sep)})"


class Strip(Processor):
    """Strip trailing spaces"""

    def __call__(self, values):
        if isinstance(values, list):
            return [v.strip() for v in values if v.strip()], {}
        return values.strip(), {}


class Collapse(Processor):
    """Collapse single element lists"""

    def __call__(self, values):
        if isinstance(values, list) and len(values) == 1:
            return values[0], {}
        return values or "", {}


class First(Processor):
    """Take first element if possible"""

    def __call__(self, values, default=""):
        if isinstance(values, list):
            return values[0], {}
        return values or default, {}


class AbsoluteUrl(Processor):
    """Urljoin element"""

    def __init__(self, base):
        self.base = base

    def __call__(self, values):
        if isinstance(values, list):
            return [urljoin(self.base, v) for v in values], {}
        return urljoin(self.base, values), {}


class Len(Processor):
    """Return length"""

    def __call__(self, values):
        return len(values), {}


class Repr(Processor):
    """return representation of value"""

    def __call__(self, values):
        return repr(values), {}


class FormatHtml(Processor):
    """Processor for pretty format of XML elements"""

    re_html = re.compile("^<.+?>")

    def format(self, element: str):
        """Format string as pretty html."""
        # skip non html elements
        if not bool(self.re_html.search(element)):
            return element
        soup = BeautifulSoup(element, features="lxml")
        text = soup.body.prettify()
        if text.startswith("<body>"):  # remove <body> wrapper
            text = "\n".join(line[1:] for line in text.splitlines()[1:-1])
        return text

    def __call__(self, values):
        if isinstance(values, list):
            return [self.format(element) for element in values], {}
        return self.format(values), {}


class Regex(Processor):
    """Regex processor that filters out non-matching values"""

    def __init__(self, pattern: str, flags=0) -> None:
        self.pattern = re.compile(pattern, flags)

    def __call__(self, values):
        if isinstance(values, list):
            return [value for value in values if self.pattern.search(value)], {}
        return values if self.pattern.search(values) else "", {}


class Slice(Processor):
    """Take slice of value."""

    def __init__(self, slice_range: str):
        self._value = slice_range.rstrip("]")
        self.slice = slice(*(int(val) if val is not None else val for val in self._value.split(":")))

    def __call__(self, values):
        return values[self.slice], {}

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._value})"
