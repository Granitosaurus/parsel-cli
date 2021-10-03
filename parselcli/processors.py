"""
Contains processor callables for parsecli
"""
from urllib.parse import urljoin


class Processor:
    """Base class for parselcli processors"""

    def __repr__(self) -> str:
        return f"{type(self).__name__}"


class Nth(Processor):
    """Take nth element of a list"""

    def __init__(self, position: int) -> None:
        self.position = int(position)

    def __call__(self, values):
        return values[self.position]

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.position})"


class Join(Processor):
    """Join multiple values with separator"""

    def __init__(self, sep=""):
        self.sep = sep

    def __call__(self, values):
        return self.sep.join(values)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({repr(self.sep)})"


class Strip(Processor):
    """Strip trailing spaces"""

    def __call__(self, values):
        if isinstance(values, list):
            return [v.strip() for v in values if v.strip()]
        return values.strip()


class Collapse(Processor):
    """Collapse single element lists"""

    def __call__(self, values):
        if isinstance(values, list) and len(values) == 1:
            return values[0]
        return values or ""


class First(Processor):
    """Take first element if possible"""

    def __call__(self, values, default=""):
        if isinstance(values, list):
            return values[0]
        return values or default


class AbsoluteUrl(Processor):
    """Urljoin element"""

    def __init__(self, base):
        self.base = base

    def __call__(self, values):
        if isinstance(values, list):
            return [urljoin(self.base, v) for v in values]
        return urljoin(self.base, values)


class Len(Processor):
    """Return length"""

    def __call__(self, values):
        return len(values)
