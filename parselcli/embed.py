# todo start shell
from collections import OrderedDict


def embed_ipython_shell(namespace=None):
    """Start an IPython Shell"""
    from IPython import embed
    embed(user_ns=namespace)


def embed_bpython_shell(namespace=None):
    """Start a bpython shell"""
    import bpython
    bpython.embed(locals_=namespace)


def embed_ptpython_shell(namespace=None):
    """Start a ptpython shell"""
    import ptpython.repl
    ptpython.repl.embed(locals=namespace)


def embed_standard_shell(namespace=None, banner=''):
    """Start a standard python shell"""
    import code
    try:  # readline module is only available on unix systems
        import readline
    except ImportError:
        pass
    else:
        import rlcompleter
        readline.parse_and_bind("tab:complete")
    code.interact(banner=banner, local=namespace)


PYTHON_SHELLS = OrderedDict([
    ('ptpython', embed_ptpython_shell),
    ('ipython', embed_ipython_shell),
    ('bpython', embed_bpython_shell),
    ('python', embed_standard_shell),
])


def embed_auto(namespace=None, preferred=None):
    if preferred:
        try:
            PYTHON_SHELLS[preferred](namespace)
            return
        except ImportError:
            print('Could not import preferred shell, fallback to defaults')
    for k, v in PYTHON_SHELLS.items():
        try:
            v(namespace)
        except ImportError:
            continue
        break

if __name__ == '__main__':
    embed_auto()
