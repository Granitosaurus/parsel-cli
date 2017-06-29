class Strip:
    def __call__(self, vs):
        if isinstance(vs, list):
            return [v.strip() for v in vs]
        return vs.strip()


class First:
    """Take first element if list has only one value"""
    def __call__(self, vs):
        if isinstance(vs, list):
            if len(vs) < 2:
                return vs[0] if vs else ''
            return vs
        return vs or ''


