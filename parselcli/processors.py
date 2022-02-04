"""
Contains processor callables for parselcli
"""
import re
from decimal import Decimal
from urllib.parse import urljoin
from typing import Tuple, Union, Dict, List

from bs4 import BeautifulSoup
from requests import Response
from loguru import logger as log


class Processor:
    """Base class for parselcli processors"""

    def __call__(
        self, values: Union[List[str], str], response: Response = None, default: str = ""
    ) -> Tuple[Union[List[str], str], Dict]:
        pass

    def __repr__(self) -> str:
        return f"{type(self).__name__}"


class Nth(Processor):
    """Take nth element of a list"""

    def __init__(self, position: int) -> None:
        self.position = int(position)

    def __call__(
        self, values: Union[List[str], str], response: Response = None, default: str = ""
    ) -> Tuple[Union[List[str], str], Dict]:
        return values[self.position], {}

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.position})"


class Join(Processor):
    """Join multiple values with separator"""

    def __init__(self, sep=""):
        self.sep = sep

    def __call__(
        self, values: Union[List[str], str], response: Response = None, default: str = ""
    ) -> Tuple[Union[List[str], str], Dict]:
        return self.sep.join(values), {}

    def __repr__(self) -> str:
        return f"{type(self).__name__}({repr(self.sep)})"


class Strip(Processor):
    """Strip trailing spaces"""

    def __init__(self, chars=None) -> None:
        self.chars = chars
        super().__init__()

    def __call__(
        self, values: Union[List[str], str], response: Response = None, default: str = ""
    ) -> Tuple[Union[List[str], str], Dict]:
        if isinstance(values, list):
            values = [v.strip(self.chars) for v in values]
            return [v for v in values if v], {}
        return values.strip(self.chars), {}


class Collapse(Processor):
    """Collapse single element lists"""

    def __call__(
        self, values: Union[List[str], str], response: Response = None, default: str = ""
    ) -> Tuple[Union[List[str], str], Dict]:
        if isinstance(values, list) and len(values) == 1:
            return values[0], {}
        return values or "", {}


class First(Processor):
    """Take first element if possible"""

    def __call__(
        self, values: Union[List[str], str], response: Response = None, default: str = ""
    ) -> Tuple[Union[List[str], str], Dict]:
        if isinstance(values, list):
            return values[0], {}
        return values or default, {}


class AbsoluteUrl(Processor):
    """Urljoin element"""

    def __call__(
        self, values: Union[List[str], str], response: Response = None, default: str = ""
    ) -> Tuple[Union[List[str], str], Dict]:
        log.debug(f"converting urls from {response} to absolute: {values}")
        if not response:
            return values, {}
        if isinstance(values, list):
            return [urljoin(response.url, v) for v in values], {}
        return urljoin(response.url, values), {}


class Len(Processor):
    """Return length"""

    def __call__(
        self, values: Union[List[str], str], response: Response = None, default: str = ""
    ) -> Tuple[Union[List[str], str], Dict]:
        return str(len(values)), {}


class Repr(Processor):
    """return representation of value"""

    def __call__(
        self, values: Union[List[str], str], response: Response = None, default: str = ""
    ) -> Tuple[Union[List[str], str], Dict]:
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

    def __call__(
        self, values: Union[List[str], str], response: Response = None, default: str = ""
    ) -> Tuple[Union[List[str], str], Dict]:
        if isinstance(values, list):
            return [self.format(element) for element in values], {}
        return self.format(values), {}


class Regex(Processor):
    """Regex processor that filters out non-matching values"""

    def __init__(self, pattern: str, flags=0) -> None:
        self.pattern = re.compile(pattern, flags)

    def check(self, value: str):
        """
        check whether value matches processor's pattern
        returns either:
        - found group if there's only 1 found group
        - list of found groups if there are any
        - value if it matches
        - "" if no matches are found
        """
        search = self.pattern.search(value)
        if not search:
            return ""
        if search.groups():
            if len(search.groups()) == 1:
                return search.groups()[0]
            return list(search.groups())
        return value

    def __call__(
        self, values: Union[List[str], str], response: Response = None, default: str = ""
    ) -> Tuple[Union[List[str], str], Dict]:
        if isinstance(values, list):
            return [self.check(value) for value in values], {}
        return self.check(values), {}


class Slice(Processor):
    """Take slice of value."""

    def __init__(self, slice_range: str):
        self._value = slice_range.rstrip("]")
        self.slice = slice(*(int(val) if val is not None else val for val in self._value.split(":")))

    def __call__(
        self, values: Union[List[str], str], response: Response = None, default: str = ""
    ) -> Tuple[Union[List[str], str], Dict]:
        return values[self.slice], {}

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._value})"


class Sum(Processor):
    """sum all values"""

    def __call__(
        self, values: Union[List[str], str], response: Response = None, default: str = ""
    ) -> Tuple[Union[List[str], str], Dict]:
        if not isinstance(values, list):
            return values, {}
        if all(v.isdigit() for v in values):
            return str(sum(int(v) for v in values)), {}
        return str(sum(Decimal(v) for v in values)), {}
