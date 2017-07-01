from urllib.parse import urljoin


class Join:
    def __call__(self, vs):
        return ''.join(vs)


class Strip:
    def __call__(self, vs):
        if isinstance(vs, list):
            return [v.strip() for v in vs]
        return vs.strip()


class First:
    """Take first element if list has only one value"""
    def __init__(self, only=False):
        self.only = only

    def __call__(self, vs):
        if isinstance(vs, list):
            if len(vs) < 2 or self.only:
                return vs[0] if vs else ''
            return vs
        return vs or ''


class UrlJoin:
    """Urljoin element"""

    def __init__(self, base):
        self.base = base

    def __call__(self, vs):
        if isinstance(vs, list):
            return [urljoin(self.base, v) for v in vs]
        return urljoin(self.base, vs)
