"""
contains command line interface functionality
"""
# pylint: disable=E1120,R0914
import os
import sys
from pathlib import Path

import click
from click import echo
from loguru import logger as log
from requests_cache import CachedSession

from parselcli.config import CONFIG, get_config
from parselcli.embed import PYTHON_SHELLS
from parselcli.prompt import Prompter

CACHE_EXPIRY = 60 * 60  # 1 hour


def setup_logging(verbosity: int = 0):
    """setup logging based on verbosity"""
    level = {0: "ERROR", 1: "INFO", 2: "DEBUG", 3: "DEBUG"}[verbosity]
    log.remove()
    log.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.S}</green> | <level>{level: <8}</level> "
        "| <cyan>{name}</cyan>:<cyan>{function}</cyan>: <level>{message}</level>",
    )


@click.command()
@click.argument("url", required=False)
@click.option("-h", "headers", help='request headers, e.g. -h "user-agent=cat bot"', multiple=True)
@click.option("-xpath", is_flag=True, help="start in xpath mode instead of css")
@click.option("-f", "--file", type=click.File("r"), help="input from html file instead of url")
@click.option("-c", "compile_css", help="compile css and return it")
@click.option("-x", "compile_xpath", help="compile xpath and return it")
@click.option("-i", "initial_input", help="initial input", multiple=True)
@click.option("--cache", help="cache requests", is_flag=True)
@click.option("--warn-limit", help="", type=click.INT)
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
    file,
    xpath,
    initial_input,
    embed,
    shell,
    compile_css,
    compile_xpath,
    cache,
    config,
    headers,
    warn_limit,
    verbosity,
):
    """Interactive shell for css and xpath selectors"""
    setup_logging(verbosity)
    headers = dict([h.split("=", 1) for h in headers])
    if not file and not url:
        echo("Either url or file argument/option needs to be provided", err=True)
        return
    if compile_css or compile_xpath:
        # disable all stdout except the result
        sys.stdout = open(os.devnull, "w")  # pylint: disable=R1732
    log.debug(f"using config from {config}")
    config = get_config(Path(config))
    log.debug(f"config values: {config}")

    # Create prompter either from url or file
    prompter_kwargs = dict(
        start_in_css=not xpath,
        preferred_embed_shell=shell,
        warn_limit=config if warn_limit is None else warn_limit,
        history_file_css=config["history_file_css"],
        history_file_xpath=config["history_file_xpath"],
        history_file_embed=config["history_file_embed"],
    )
    if url:
        if cache:
            echo(f"using cached version for: {url}")
        else:
            echo(f"requesting: {url}")
        cache_expire = config["requests"]["cache_expire"] if cache else 0
        req_config = {k: v for k, v in config["requests"].items() if k in ["headers"]}
        log.debug(f"inferred headers from config: {req_config['headers']}")
        log.debug(f"inferred headers from cli: {headers}")
        headers = {**req_config["headers"], **headers}
        log.debug(f"using combined headers: {headers}")
        with CachedSession(config["requests"]["cache_file"], expire_after=cache_expire) as session:
            resp = session.get(url, headers=headers)
        prompter = Prompter.from_response(response=resp, **prompter_kwargs)
    else:
        echo(f"using local file: {file}")
        prompter = Prompter.from_file(file, **prompter_kwargs)

    if not initial_input:
        initial_input = config.get("initial_input", [])
    if initial_input:
        for line in initial_input:
            prompter.readline(line)
    if compile_css:
        log.debug(f'compiling css "{compile_css}" and exiting')
        sys.stdout = sys.__stdout__  # enable stdout for results
        echo(prompter.get_css(compile_css))
        return
    if compile_xpath:
        log.debug(f'compiling xpath "{compile_xpath}" and exiting')
        sys.stdout = sys.__stdout__
        echo(prompter.get_xpath(compile_xpath))
        return
    log.debug("starting prompt loop")
    prompter.loop_prompt(start_in_embed=embed)


if __name__ == "__main__":
    cli()
