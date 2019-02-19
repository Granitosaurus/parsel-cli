# parsel-cli

Parsel-cli is a command line interface wrapper for [parsel](https://github.com/scrapy/parsel) package for evaluating css and xpath selection real time.
> Parsel is a library to extract data from HTML and XML using XPath and CSS selectors



## Usage

    Usage: parsel [OPTIONS] [URL]

    Options:
      -xpath                          start in xpath mode instead of css
      -fstrip                         enable strip processor flag
      -ffirst                         enable first processor flag
      -fabsolute                      enable absolute url processor flag
      -fjoin                          enable only join processor flag
      -f, --file FILENAME             input from html file instead of url
      -c TEXT                         compile css and return it
      -x TEXT                         compile xpath and return it
      --cache                         cache requests
      --embed                         start in embedded python shell
      --shell [ptpython|ipython|bpython|python]
                                      preferred embedded shell; default auto
                                      resolve in order
      --help                          Show this message and exit.


Parsel-cli reads XML or HTML file from url or disk and starts interpreter for xpath or css selectors.
By default it starts in xpath interpreter mode but can be switched by `css` command and switched back with `xpath`.

The interpreter also supports commands and embedding of `python`, `ptpython`, `ipython` and `bpython` shells.
Command can be called with `-` prefix. List of available commands can be found by calling `-help` command (see Example section).

Parsel-cli also supports output processors that can be activated with `+` prefix and deactivated with `-`.
Available processors:

    +-strip - strip all values of trailing and leading spaces and newlines

Parcel-cli also supports tab complete and history powered by `prompt-toolkit` (history is stored in ~/.parsel_history)

## Example

    $ parsel "https://news.ycombinator.com/item?id=19187417"
    > .athing .title a::text
    ['LD_PRELOAD: The Hero We Need and Deserve']

There are also processors for readability:

    > +first
    enabled flag: first
    > .athing .title a::text
    LD_PRELOAD: The Hero We Need and Deserve
    
also supports xpath:

    > -xpath
    switched to xpath
    > //a[contains(text(),'LD_PRELOAD')]/text()
    LD_PRELOAD: The Hero We Need and Deserve

Also supports commands!

    > -fetch https://news.ycombinator.com/news
    downloading https://news.ycombinator.com/news
    > +first
    enabled flag: first
    > .athing .title a::text                                                                                             
    Bookworm: A Simple, Focused eBook Reader

See more for help:

    > -help                                                                                                              
    available commands (use -command):
      help: show help
      debug: show debug info
      embed: start interactive python shell
      view: open current file in browser tab
      fetch: download from new url
      css: switch to css selectors
      xpath: switch to xpath selectors
    available flags (use +flag to enable and -flag to disable)
      strip: strip every element of trailing and leading spaces
      first: take first element when there's only one
      collapse: collapse lists when only 1 element
      absolute: convert relative urls to absolute
      join: join results into one

    
## Install

    pip install --user git+https://github.com/Granitosaurus/parsel-cli@v0.26
