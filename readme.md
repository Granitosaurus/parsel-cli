
# About parselcli ![PyPI](https://img.shields.io/pypi/v/parselcli.svg?style=popout)

`parselcli` is a command line interface wrapper for [parsel](https://github.com/scrapy/parsel) package for evaluating css and xpath selection real time against web urls or local html files.  
> Parsel is a library to extract data from HTML and XML using XPath and CSS selectors

[![asciicast](https://asciinema.org/a/234118.svg)](https://asciinema.org/a/234118)

#### Features:

* Supports css and xpath expression.
* Interactive shell with autocomplete.
* Css and xpath hints based on current webpage DOM.
* Full input history.
* Cache support for repeated usage.
* Extensive and instant text processing via text processor flags.

## Usage

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

`parsecli` supports flags and commands in shell: 

    $ parsel "https://github.com/granitosaurus/parsel-cli"                                                               
    > -help                                                                                                              
    available commands (use -command):
      help: show help
      debug: show debug info
      embed: start interactive python shell
      open: open current url in browser tab
      view: open current html in browser tab
      fetch: download from new url
      css: switch to css selectors
      xpath: switch to xpath selectors
    available flags (use +flag to enable and -flag to disable)
      strip: strip every element of trailing and leading spaces
      first: take first element when there's only one
      collapse: collapse lists when only 1 element
      absolute: convert relative urls to absolute
      join: join results into one
      len: return length of results


Processors can be activated with `+` prefix and deactivated with `-`. These processors can be supplied inline:

    > h1::text +strip
    ['parsel-cli']
    
    
or activated for whole session
    
    > +strip 
    enabled flag: strip

Commands are just called as is with sometimes taking a positional argument:

    > -fetch "http://some-other-url.com"
    downloading "http://some-other-url.com"
    > -view
    opening document in browser

## Example

    $ parsel "https://github.com/granitosaurus/parsel-cli"                                                               
    > h1::text                                                                                                           
    ['\n  ', '\n  ', '\n\n', 'parsel-cli']
    > +join +strip                                                                                                       
    enabled flag: join
    enabled flag: strip
    > h1::text                                                                                                           
    parsel-cli
    > h1::text +len                                                                                                      
    4
    > -xpath                                                                                                             
    switched to xpath
    > //h1/text()                                                                                                        
    parsel-cli
    > -css                                                                                                               
    switched to css
    > -embed                                                                                                             
    >>> locals()                                                                                                         
    {'sel': <Selector xpath=None data='<html lang="en">\n  <head>\n    <meta char'>, 'response': <Response [200]>, 'request': <PreparedRequest [GET]>, '_': {...}, '_1': {...}}


    >>> response                                                                                                         
    <Response [200]>


    >>>                                                                                                                  
    > -debug                                                                                                             
    200-https://github.com/granitosaurus/parsel-cli
    enabled processors:
      Join
      Strip
    > -help                                                                                                              
    available commands (use -command):
      help: show help
      debug: show debug info
      embed: start interactive python shell
      open: open current url in browser tab
      view: open current html in browser tab
      fetch: download from new url
      css: switch to css selectors
      xpath: switch to xpath selectors
    available flags (use +flag to enable and -flag to disable)
      strip: strip every element of trailing and leading spaces
      first: take first element when there's only one
      collapse: collapse lists when only 1 element
      absolute: convert relative urls to absolute
      join: join results into one
      len: return length of results

    
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
    cache_dir = "/home/user/.cache/parsel/requests.cache"

    [requests.headers]
    # here headers can be defined for requests to avoid bot detection etc.
    User-Agent = "parselcli web inspector"
    # e.g. chrome on windows use
    # User-Agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"

 
