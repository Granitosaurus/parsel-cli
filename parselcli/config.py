import os
import toml
from pathlib import Path

XDG_CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
XDG_CACHE_HOME = Path(os.environ.get('XDG_CACHE_HOME') or "~/.cache").expanduser()

APP_NAME = 'parsel'
CONFIG = XDG_CONFIG_HOME / 'parsel.toml'
CACHE_DIR = XDG_CACHE_HOME / APP_NAME


DEFAULT_CONFIG = {
    'processors': ['collapse', 'strip'],
    'history_file': str(CACHE_DIR / 'history'),
    'requests':
        {
            'headers': {
                'User-Agent': 'parselcli web inspector',
            },
            'cache_expire': 86400,
            'cache_dir': str(CACHE_DIR / 'requests.cache'),
        }
}


def init_config(config_dir=None):
    if not config_dir:
        config_dir = CONFIG
    with open(config_dir, 'w') as f:
        toml.dump(DEFAULT_CONFIG, f)


def get_config(config_dir=None):
    """returns config file from config directory. Any unset values default to DEFAULT_CONFIG configuration"""
    if not config_dir:
        config_dir = CONFIG
    if not config_dir.exists():
        init_config()
    with open(config_dir, 'r') as f:
        config = {**DEFAULT_CONFIG, **toml.loads(f.read())}
    Path(config['requests']['cache_dir']).mkdir(exist_ok=True, parents=True)
    Path(config['history_file']).touch(exist_ok=True)
    return config

