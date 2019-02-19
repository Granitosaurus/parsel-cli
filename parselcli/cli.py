import os

import click
import requests
import sys
from click import echo
from requests_cache import CachedSession

from parselcli.app import REQUESTS_CACHE
from parselcli.prompt import Prompter
from parselcli.embed import PYTHON_SHELLS


CACHE_EXPIRY = 60 * 60  # 1 hour
@click.command()
@click.argument('url', required=False)
@click.option('-xpath', is_flag=True,
              help='start in xpath mode instead of css')
@click.option('-fstrip', is_flag=True,
              help='enable strip processor flag')
@click.option('-ffirst', is_flag=True,
              help='enable first processor flag')
@click.option('-fabsolute', is_flag=True,
              help='enable absolute url processor flag')
@click.option('-fjoin', is_flag=True,
              help='enable only join processor flag')
@click.option('-f', '--file', type=click.File('r'),
              help='input from html file instead of url')
@click.option('-c', 'compile_css',
              help='compile css and return it')
@click.option('-x', 'compile_xpath',
              help='compile xpath and return it')
@click.option('--cache', help='cache requests', is_flag=True)
@click.option('--embed', is_flag=True,
              help='start in embedded python shell')
@click.option('--shell', type=click.Choice(list(PYTHON_SHELLS.keys())),
              help='preferred embedded shell; default auto resolve in order')
def cli(url, file, xpath, fstrip, ffirst, fjoin, fabsolute, embed, shell, compile_css, compile_xpath, cache):
    if not file and not url:
        echo('Either url or file argument/option needs to be provided', err=True)
        return
    if compile_css or compile_xpath:
        # disable all stdout except the result
        sys.stdout = open(os.devnull, 'w')

    # Determine flags to use
    flags = {
        'strip': fstrip,
        'first': ffirst,
        'absolute': fabsolute,
        'join': fjoin,
    }
    enabled_flags = [k for k, v in flags.items() if v]
    # Create prompter either from url or file
    if url:
        if cache:
            echo('using cached version')
        with CachedSession(str(REQUESTS_CACHE), expire_after=CACHE_EXPIRY if cache else 0) as session:
            resp = session.get(url)
        prompter = Prompter.from_response(
            response=resp,
            preferred_embed_shell=shell,
            start_in_css=not xpath,
            flags=enabled_flags)
    else:
        prompter = Prompter.from_file(file, preferred_embed=shell, start_in_css=not xpath, flags=enabled_flags)

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
