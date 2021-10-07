"""
contains user configuration functionality
"""
import os
from pathlib import Path

import toml

from parselcli.utils import lazy_dict_merge

XDG_CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
XDG_CACHE_HOME = Path(os.environ.get("XDG_CACHE_HOME") or "~/.cache").expanduser()

APP_NAME = "parsel"
CONFIG = XDG_CONFIG_HOME / "parsel.toml"
CACHE_DIR = XDG_CACHE_HOME / APP_NAME

DEFAULT_CONFIG = {
    # default processors that are activated on startup
    "color": True,
    "vi_mode": False,
    "warn_limit": 5000,
    "initial_input": [],
    "history_file_css": str(CACHE_DIR / "history_css"),
    "history_file_xpath": str(CACHE_DIR / "history_xpath"),
    "history_file_embed": str(CACHE_DIR / "history_embed"),
    "requests": {
        "headers": {
            # default headers most web browser use
            # using windows chrome user agent as it's the most popular one
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9,lt;q=0.8,et;q=0.7,de;q=0.6",
        },
        "cache_expire": 86400,
        "cache_file": str(CACHE_DIR / "requests.cache"),
    },
}


def init_default_config(config_dir=None):
    """Create config"""
    if not config_dir:
        config_dir = CONFIG
    with open(config_dir, "w") as f:
        toml.dump(DEFAULT_CONFIG, f)


def update_config(config, config_dir=None):
    """update disk config with current config object"""
    if not config_dir:
        config_dir = CONFIG
    updated_config = lazy_dict_merge(config, DEFAULT_CONFIG)
    with open(config_dir, "w") as f:
        toml.dump(updated_config, f)
    return updated_config


def get_config(config_dir=None):
    """returns config file from config directory. Any unset values default to DEFAULT_CONFIG configuration"""
    if not config_dir:
        config_dir = CONFIG
    if not config_dir.exists():
        init_default_config()
    with open(config_dir, "r") as f:
        config = toml.loads(f.read())
    config = update_config(config, config_dir=config_dir)
    # ensure history and cache files exists
    Path(config["requests"]["cache_file"]).parent.mkdir(exist_ok=True, parents=True)
    Path(config["requests"]["cache_file"]).touch(exist_ok=True)
    Path(config["history_file_css"]).touch(exist_ok=True)
    Path(config["history_file_xpath"]).touch(exist_ok=True)
    return config
