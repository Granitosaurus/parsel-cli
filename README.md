
# About parselcli ![PyPI](https://img.shields.io/pypi/v/parselcli.svg?style=popout)

`parselcli` is a command line interface wrapper for [parsel](https://github.com/scrapy/parsel) package for evaluating css and xpath selection real time against web urls or local html files.  

> Parsel is a library to extract data from HTML and XML using XPath and CSS selectors

## Example Usage

Calling command `parsel` with any http url will drop terminal into prompt. 
In the prompt css and xpath selector can be entered together with commands and processing options

```
$ parsel "https://github.com/granitosaurus/parsel-cli"
> h1::text
['\n    ', '\n  ', '\n  ', '\n  ', '\n\n  ', '\n', 'About parselcli ']
> --xpath
> //h1/text()
['\n    ', '\n  ', '\n  ', '\n  ', '\n\n  ', '\n', 'About parselcli ']
> --css
> --join --strip
default processors: [Join, Strip]
> h1::text
About parselcli
> h1::text --len
7
> --xpath
switched to xpath
default processors: [Join, Strip]
> //h1/text()
About parselcli
> --css
switched to css
default processors: [Join, Strip]
```
 

#### Features:

* Supports css and xpath expression.
* Interactive shell with autocomplete.
* Css and xpath hints based on current webpage DOM.
* Input history tracking
* Cache support for repeated usage.
* Extensive and instant text processing via text processor flags.

## Details

    $ parsel --help                                                                                                      
    Usage: parsel [OPTIONS] [URL]

      Interactive shell for css and xpath selectors

    Options:
      -h TEXT                         request headers, e.g. -h "user-agent=cat
                                      bot"
      -xpath                          start in xpath mode instead of css
      -p, --processors TEXT           comma separated processors: {}
      -f, --file FILENAME             input from html file instead of url
      -c TEXT                         compile css and return it
      -x TEXT                         compile xpath and return it
      --cache                         cache requests
      --config TEXT                   config file  [default:
                                      /home/dex/.config/parsel.toml]
      --embed                         start in embedded python shell
      --shell [ptpython|ipython|bpython|python]
                                      preferred embedded shell; default auto
                                      resolve in order
      --help                          Show this message and exit.


`parselcli` reads XML or HTML file from url or disk and starts interpreter for xpath or css selectors.
By default it starts in css interpreter mode but can be switched to xpath by `-xpath` command and switched back with `-css`.
Interpreter also has auto complete and suggestions for selectors \[in progress\]

The interpreter also supports commands and embedding of `python`, `ptpython`, `ipython` and `bpython` shells.
Command can be called with `-` prefix. List of available commands can be found by calling `-help` command (see Example section).



### Processors and Commands

`parsecli` supports processors and commands in shell for advance usage:

    $ parsel "https://github.com/granitosaurus/parsel-cli"                                                               
    > --help                                                                                                              
    Commands:
    --help                   print help
    --embed                  embed repl
    --info                   show context info
    --css                    switch to css input
    --xpath                  siwtch to xpath input
    --open                   open current url in web browser
    --view                   open current doc in web browser
    Processors:
    --first, -1              take only 1st value
    --len, -l                return total length
    --strip, -s              strip away trailing chars
    --absolute, -a           turn relative urls to absolute ones
    --collapse, -c           collapse single element lists
    --join, -j               join results
    --join-with, -J          join results with specified character
    -n                       take n-th element

Commands can be called at any point in the prompter:

    > -fetch "http://some-other-url.com"
    downloading "http://some-other-url.com"
    > -view
    opening document in browser

Processor options can be either activated for specific prompt:

    > h1::text --first
    # will take first element

Or can be set for current session:
    > --first
    default processors: [First]
    # will process every following command with new processors

## Install
    
    pip install parselcli
    
or install from github:

    pip install --user git+https://github.com/Granitosaurus/parsel-cli@v0.33
    
## Config

`parselcli` can be configured via `toml` configuration file found in `$XDG_HOME/parsel.toml` (usually `~/.config/parsel.toml`):

    # default processors (the +flags)
    processors = [ "collapse", "strip",]
    # where ptpython history is located
    history_file_css = "/home/user/.cache/parsel/history_css"
    history_file_xpath = "/home/user/.cache/parsel/history_xpath"
    history_file_embed = "/home/user/.cache/parsel/history_embed"
    
    [requests]
    # when using --cache flag for using cached responses
    cache_expire = 86400
    # where sqlite cache file is stored for cache
    cache_file = "/home/user/.cache/parsel/requests.cache"

    [requests.headers]
    # here headers can be defined for requests to avoid bot detection etc.
    User-Agent = "parselcli web inspector"
    # e.g. chrome on windows use
    # User-Agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"

 
