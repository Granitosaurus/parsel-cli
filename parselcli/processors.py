
class Strip:
    def __call__(self, vs):
        if isinstance(vs, list):
            return [v.strip() for v in vs]
        return vs.strip()

if __name__ == '__main__':
    s = Strip()
    print(type(s).__name__)
