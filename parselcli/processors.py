from urllib.parse import urljoin


class Join:
    def __init__(self, sep=''):
        self.sep = sep

    def __call__(self, vs):
        return self.sep.join(vs)


class Strip:
    def __call__(self, vs):
        if isinstance(vs, list):
            return [v.strip() for v in vs if v.strip()]
        return vs.strip()


class Collapse:
    def __call__(self, vs):
        if isinstance(vs, list) and len(vs) == 1:
            return vs[0]
        return vs or ''


class First:
    """Take first element"""

    def __call__(self, vs):
        if isinstance(vs, list):
            return vs[0]
        return vs or ''


class AbsoluteUrl:
    """Urljoin element"""

    def __init__(self, base):
        self.base = base

    def __call__(self, vs):
        if isinstance(vs, list):
            return [urljoin(self.base, v) for v in vs]
        return urljoin(self.base, vs)


class Len:
    """Return length"""

    def __call__(self, vs):
        return len(vs)


