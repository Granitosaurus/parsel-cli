"""
Contains command line interface functionality.
This is the entrypoint for parselcli cli app.
"""
# pylint: disable=E1120,R0914
from functools import partial
import sys
from pathlib import Path

import click
from click import echo
from loguru import logger as log

from parselcli.config import CONFIG, get_config
from parselcli.embed import PYTHON_SHELLS
from parselcli.prompt import Prompter
from parselcli.render.browser import PlaywrightRenderer
from parselcli.render.http import HttpRenderer, CachedHttpRenderer

CACHE_EXPIRY = 60 * 60  # 1 hour

echo = partial(echo, err=True)


def setup_logging(verbosity: int = 0):
    """setup logging based on verbosity."""
    level = {0: "ERROR", 1: "INFO", 2: "DEBUG", 3: "DEBUG"}[verbosity]
    log.remove()
    log.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.S}</green> | <level>{level: <8}</level> "
        "| <cyan>{name}</cyan>:<cyan>{function}</cyan>: <level>{message}</level>",
    )


@click.command()
@click.argument("url")
@click.option("-h", "headers", help='request headers, e.g. -h "user-agent=cat bot"', multiple=True)
@click.option("--xpath", is_flag=True, help="start in xpath mode instead of css")
@click.option("--browser", is_flag=True, help="use browser emulator")
@click.option("--browser-headless", is_flag=True, help="use headless browser emulator")
@click.option(
    "--browser-wait",
    type=click.Choice(["load", "domcontentloaded", "networkidle", "none"]),
    help="wait for browser page to reach some state",
    default="domcontentloaded",
)
@click.option(
    "--browser-wait-css",
    help="wait for browser page to render until css selector appears",
)
@click.option(
    "--browser-wait-xpath",
    help="wait for browser page to render until xpath selector appears",
)
@click.option("-c", "compile_css", help="compile css and return it")
@click.option("-x", "compile_xpath", help="compile xpath and return it")
@click.option("-i", "initial_input", help="initial input", multiple=True)
@click.option("--cache", help="cache requests", is_flag=True)
@click.option("--no-color", help="disable html output colors", is_flag=True)
@click.option("--vi-mode", help="enable vi-mode for input", is_flag=True)
@click.option("--config", help="config file", default=CONFIG, show_default=True)
@click.option("--embed", is_flag=True, help="start in embedded python shell")
@click.option("-v", "verbosity", help="verbosity level", count=True)
@click.option(
    "--shell",
    type=click.Choice(list(PYTHON_SHELLS.keys())),
    help="preferred embedded shell; default auto resolve in order",
)
def cli(
    url,
    xpath,
    initial_input,
    embed,
    shell,
    compile_css,
    compile_xpath,
    cache,
    config,
    headers,
    verbosity,
    no_color,
    vi_mode,
    browser,
    browser_headless,
    browser_wait,
    browser_wait_css,
    browser_wait_xpath,
):
    """Interactive shell for css and xpath selectors"""
    setup_logging(verbosity)
    echo(f"using cached version for: {url}" if cache else f"requesting: {url}")
    log.debug(f"using config from {config}")
    headers = dict([h.split("=", 1) for h in headers])
    config = get_config(Path(config))
    log.debug(f"config values: {config}")

    # Create prompter either from url or file
    req_config = {k: v for k, v in config["requests"].items() if k in ["headers"]}
    log.debug(f"inferred headers from config: {req_config['headers']}")
    log.debug(f"inferred headers from cli: {headers}")
    headers = {**req_config["headers"], **headers}
    log.debug(f"using headers: {headers}")

    # Establish renderer
    if browser or browser_headless:
        renderer_cls = PlaywrightRenderer
    elif cache:
        renderer_cls = CachedHttpRenderer
    else:
        renderer_cls = HttpRenderer
    renderer = renderer_cls(
        headers=headers,
        cache_file=config["requests"]["cache_file"],
        cache_expire=config["requests"]["cache_expire"] if cache else -1,
        browser_kwargs={"headless": bool(browser_headless)},
    )
    renderer.open()
    renderer.goto(url)
    if browser:
        if browser_wait:
            log.debug(f"faiting for load state: {browser_wait}")
            renderer.page.wait_for_load_state(browser_wait)
        if browser_wait_css:
            log.debug(f"faiting for css selector: {browser_wait_xpath}")
            renderer.page.wait_for_selector(browser_wait_css)
        if browser_wait_xpath:
            log.debug(f"faiting for xpath selector: {browser_wait_xpath}")
            renderer.page.wait_for_selector(browser_wait_xpath)

    prompter_kwargs = dict(
        start_in_css=not xpath,
        history_file_css=config["history_file_css"],
        history_file_xpath=config["history_file_xpath"],
        history_file_embed=config["history_file_embed"],
        color=not (not config["color"] or no_color),
        vi_mode=vi_mode or config["vi_mode"],
        preferred_embed=shell,
    )
    prompter = Prompter(renderer=renderer, **prompter_kwargs)

    if not initial_input:
        initial_input = config.get("initial_input", [])
    if initial_input:
        for line in initial_input:
            prompter.readline(line)
    if compile_css:
        log.debug(f'compiling css "{compile_css}" and exiting')
        prompter.console.print(prompter.readline(compile_css + " --css")[0])
        return
    if compile_xpath:
        log.debug(f'compiling xpath "{compile_xpath}" and exiting')
        prompter.console.print(prompter._get_xpath(compile_xpath)[0])
        return
    log.debug("starting prompt loop")
    try:
        prompter.loop_prompt(start_in_embed=embed)
    except Exception as e:
        prompter.renderer.close()
        raise e


if __name__ == "__main__":
    cli()
