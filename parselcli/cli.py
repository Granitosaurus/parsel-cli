import click
import requests
from click import echo
from parselcli.prompt import Prompter
from parselcli.embed import PYTHON_SHELLS


@click.command()
@click.argument('url', required=False)
@click.option('-css', is_flag=True,
              help='start in css mode instead of xpath')
@click.option('-strip', is_flag=True,
              help='enable strip processor')
@click.option('-f', '--file', type=click.File('r'),
              help='input from html file instead of url')
@click.option('--embed', is_flag=True,
              help='start in embedded python shell')
@click.option('--shell', type=click.Choice(list(PYTHON_SHELLS.keys())),
              help='preferred embedded shell; default auto resolve in order')
def cli(url, file, css, strip, embed, shell):
    if not file and not url:
        echo('Either url or file argument/option needs to be provided', err=True)
        return
    if url:
        resp = requests.get(url)
        source = resp.text
    else:
        resp = None
        source = file.read()
    prompter = Prompter(text=source, response=resp, preferred_embed=shell,
                        start_in_css=css, flag_strip=strip)
    prompter.start_prompt_mode(start_in_embed=embed)


if __name__ == '__main__':
    cli()
