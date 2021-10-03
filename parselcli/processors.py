from urllib.parse import urljoin


class Processor:
    def __repr__(self) -> str:
        return f"{type(self).__name__}"


class Nth(Processor):
    def __init__(self, n: int) -> None:
        self.n = int(n)

    def __call__(self, vs):
        return vs[self.n]

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.n})"


class Join(Processor):
    def __init__(self, sep=""):
        self.sep = sep

    def __call__(self, vs):
        return self.sep.join(vs)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({repr(self.sep)})"


class Strip(Processor):
    def __call__(self, vs):
        if isinstance(vs, list):
            return [v.strip() for v in vs if v.strip()]
        return vs.strip()


class Collapse(Processor):
    def __call__(self, vs):
        if isinstance(vs, list) and len(vs) == 1:
            return vs[0]
        return vs or ""


class First(Processor):
    def __call__(self, vs):
        if isinstance(vs, list):
            return vs[0]
        return vs or ""


class AbsoluteUrl(Processor):
    """Urljoin element"""

    def __init__(self, base):
        self.base = base

    def __call__(self, vs):
        if isinstance(vs, list):
            return [urljoin(self.base, v) for v in vs]
        return urljoin(self.base, vs)


class Len(Processor):
    """Return length"""

    def __call__(self, vs):
        return len(vs)
