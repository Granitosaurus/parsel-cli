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

## Example

    parsel "https://github.com/Granitosaurus/parsel-cli"
    > -help
    available commands (use -command):
      help
      debug
    available flags (use +flag to enable and -flag to disable)
      strip
    > css
    switching to css
    > span.author a::text
    ['Granitosaurus']
    > xpath
    switching to xpath
    > //span[@class='author']//text()
    ['Granitosaurus']

## Install

    pip install git+https://github.com/Granitosaurus/parsel-cli
