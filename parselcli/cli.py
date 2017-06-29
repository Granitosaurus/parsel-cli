import os

import click
import requests
import sys
from click import echo
from parselcli.prompt import Prompter
from parselcli.embed import PYTHON_SHELLS


@click.command()
@click.argument('url', required=False)
@click.option('-css', is_flag=True,
              help='start in css mode instead of xpath')
@click.option('-fstrip', is_flag=True,
              help='enable strip processor flag')
@click.option('-ffirst', is_flag=True,
              help='enable first processor flag')
@click.option('-f', '--file', type=click.File('r'),
              help='input from html file instead of url')
@click.option('-c', 'compile_css',
              help='compile css and return it')
@click.option('-x', 'compile_xpath',
              help='compile xpath and return it')
@click.option('--embed', is_flag=True,
              help='start in embedded python shell')
@click.option('--shell', type=click.Choice(list(PYTHON_SHELLS.keys())),
              help='preferred embedded shell; default auto resolve in order')
def cli(url, file, css, fstrip, ffirst, embed, shell, compile_css, compile_xpath):
    if not file and not url:
        echo('Either url or file argument/option needs to be provided', err=True)
        return
    if compile_css or compile_xpath:
        # disable all stdout except the result
        sys.stdout = open(os.devnull, 'w')
    if url:
        resp = requests.get(url)
        source = resp.text
    else:
        resp = None
        source = file.read()
    flags = []
    if fstrip:
        flags.append('strip')
    if ffirst:
        flags.append('first')
    prompter = Prompter(text=source, response=resp, preferred_embed=shell,
                        start_in_css=css, flags=flags)
    if compile_css:
        sys.stdout = sys.__stdout__  # enable stdout for results
        print(prompter.get_css(compile_css))
        return
    if compile_xpath:
        sys.stdout = sys.__stdout__
        print(prompter.get_xpath(compile_xpath))
        return
    prompter.start_prompt_mode(start_in_embed=embed)


if __name__ == '__main__':
    cli()
