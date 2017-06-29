# parsel-cli

Parsel-cli is a command line interface wrapper for [parsel](https://github.com/scrapy/parsel) package.
> Parsel is a library to extract data from HTML and XML using XPath and CSS selectors

## Usage

    Usage: parsel [OPTIONS] [URL]

    Options:
      -css                 start in css mode
      -strip               enable strip processor
      -f, --file FILENAME  Input from html file
      --help               Show this message and exit.

Parsel-cli reads XML or HTML file from url or disk and starts interpreter for xpath or css selectors.
By default it starts in xpath interpreter mode but can be switched by `css` command and switched back with `xpath`.

The interpreter also supports commands and embedding of `python`, `ptpython`, `ipython` and `bpython` shells.
Command can be called with `-` prefix. List of available commands can be found by calling `-help` command (see Example section).

Parsel-cli also supports output processors that can be activated with `+` prefix and deactivated with `-`.
Available processors:

    +-strip - strip all values of trailing and leading spaces and newlines

Parcel-cli also supports tab complete and history powered by `prompt-toolkit` (history is stored in ~/.parsel_history)

## Example


    $ parsel "https://github.com/Granitosaurus/parsel-cli"
    > -help
    available commands (use -command):
      help
      debug
      embed
    available flags (use +flag to enable and -flag to disable)
      strip
    > //span[@class='author']//text()
    ['Granitosaurus']
    > css
    switching to css
    > span.author a::text
    ['Granitosaurus']
    > +strip
    enabled flag: strip
    > -embed
    >>> dir()
    ['__builtins__', 'request', 'response', 'sel']
    >>> sel.css("span.author a::text").extract_first().upper()
    'GRANITOSAURUS'

## Install

    pip install git+https://github.com/Granitosaurus/parsel-cli
