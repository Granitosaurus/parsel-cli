"""
contains helpers for shell embeding
"""
# pylint: disable=C0415,W0613,E0401
from collections import OrderedDict


def embed_ipython_shell(namespace=None, history_filename=None):
    """Start an IPython Shell"""
    from IPython import embed
    from IPython.terminal.ipapp import load_default_config
    import nest_asyncio

    nest_asyncio.apply()

    c = load_default_config()
    c.HistoryAccessor.hist_file = history_filename
    c.InteractiveShellEmbed = c.TerminalInteractiveShell
    embed(user_ns=namespace, using="asyncio", config=c)


def embed_standard_shell(namespace=None, banner="", history_filename=None):
    """Start a standard python shell"""
    import code

    try:  # readline module is only available on unix systems
        import readline
    except ImportError:
        readline.parse_and_bind("tab:complete")

    code.interact(banner=banner, local=namespace)


PYTHON_SHELLS = OrderedDict(
    [
        ("ipython", embed_ipython_shell),
        ("python", embed_standard_shell),
    ]
)


def embed_auto(namespace=None, preferred=None, history_filename=None):
    """
    Detect and embed first shell available in priority configuration
    """
    if preferred:
        try:
            PYTHON_SHELLS[preferred](namespace, history_filename=history_filename)
            return
        except ImportError:
            print("Could not import preferred shell, fallback to defaults")
    for shell_callable in PYTHON_SHELLS.values():
        try:
            shell_callable(namespace, history_filename=history_filename)
        except ImportError:
            continue
        break
