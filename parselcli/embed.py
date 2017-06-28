# todo start shell
from collections import OrderedDict


def embed_ipython_shell(namespace={}):
    """Start an IPython Shell"""
    from IPython import embed
    embed(user_ns=namespace)


def embed_bpython_shell(namespace={}):
    """Start a bpython shell"""
    import bpython
    bpython.embed(locals_=namespace)


def embed_ptpython_shell(namespace={}):
    """Start a ptpython shell"""
    import ptpython.repl
    ptpython.repl.embed(locals=namespace)


def embed_standard_shell(namespace={}, banner=''):
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


def embed_auto():
    pass
