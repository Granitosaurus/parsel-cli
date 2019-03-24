import os

import click
import sys
from click import echo
from requests_cache import CachedSession

from parselcli.config import get_config, CONFIG
from parselcli.prompt import Prompter
from parselcli.embed import PYTHON_SHELLS

CACHE_EXPIRY = 60 * 60  # 1 hour


@click.command()
@click.argument('url', required=False)
@click.option('-h', 'headers',
              help='request headers, e.g. -h "user-agent=cat bot"',
              multiple=True)
@click.option('-xpath', is_flag=True,
              help='start in xpath mode instead of css')
@click.option('-p', '--processors', default='',
              help='comma separated processors: {}')
@click.option('-f', '--file', type=click.File('r'),
              help='input from html file instead of url')
@click.option('-c', 'compile_css',
              help='compile css and return it')
@click.option('-x', 'compile_xpath',
              help='compile xpath and return it')
@click.option('--cache', help='cache requests', is_flag=True)
@click.option('--config', help='config file', default=CONFIG, show_default=True)
@click.option('--embed', is_flag=True,
              help='start in embedded python shell')
@click.option('--shell', type=click.Choice(list(PYTHON_SHELLS.keys())),
              help='preferred embedded shell; default auto resolve in order')
def cli(url, file, xpath, processors, embed, shell, compile_css, compile_xpath, cache, config, headers):
    """Interactive shell for css and xpath selectors"""
    headers = [h.split('=', 1) for h in headers]
    headers = {k: v for k, v in headers}
    if not file and not url:
        echo('Either url or file argument/option needs to be provided', err=True)
        return
    if compile_css or compile_xpath:
        # disable all stdout except the result
        sys.stdout = open(os.devnull, 'w')
    config = get_config(config)

    # Determine flags to use
    processors = [p for p in processors.split(',') if p]
    if not processors:
        config.get('processors', [])
    for processor in processors:
        if processor not in Prompter.available_flags:
            echo(f'unknown processor "{processor}", must be one of: {", ".join(Prompter.available_flags)}', err=True)
            exit(1)

    # Create prompter either from url or file
    prompter_kwargs = dict(
        start_in_css=not xpath,
        flags=processors,
        preferred_embed_shell=shell,
        history_file_css=config['history_file_css'],
        history_file_xpath=config['history_file_xpath'],
    )
    if url:
        if cache:
            echo('using cached version')
        cache_expire = config['requests']['cache_expire'] if cache else 0
        req_headers = {k: v for k, v in config['requests'].items() if k in ['headers']}
        req_headers['headers'].update(headers)
        with CachedSession(config['requests']['cache_dir'], expire_after=cache_expire) as session:
            resp = session.get(url, **req_headers)
        prompter = Prompter.from_response(response=resp, **prompter_kwargs)
    else:
        prompter = Prompter.from_file(file, **prompter_kwargs)

    if compile_css:
        sys.stdout = sys.__stdout__  # enable stdout for results
        print(prompter.get_css(compile_css))
        return
    if compile_xpath:
        sys.stdout = sys.__stdout__
        print(prompter.get_xpath(compile_xpath))
        return
    prompter.loop_prompt(start_in_embed=embed)


if __name__ == '__main__':
    cli()
