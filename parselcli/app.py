import os
from pathlib import Path

APP_NAME = 'parsel'
XDG_CACHE_HOME = Path(os.environ.get('XDG_CACHE_HOME') or "~/.cache").expanduser()
CACHE_DIR = XDG_CACHE_HOME / APP_NAME
REQUESTS_CACHE = CACHE_DIR / 'requests.cache'
HISTORY = CACHE_DIR / 'history'

CACHE_DIR.mkdir(exist_ok=True)
HISTORY.touch(exist_ok=True)
