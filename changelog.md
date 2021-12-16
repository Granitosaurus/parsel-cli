UNRELEASED [1.2.0]
- add support for rendering target in browser emulator via `--browser` flag.  
    This feature requires optional dependency [playwright](https://github.com/microsoft/playwright-python), can be installed via `pip install parselcli[browser]`.
    When `--browser` flag is used, a temporary playwright controlled headless browser will be launched and attached to parsel session.
- add support for browser load instructions via `--browser-
- add `--clipin` and `--clipout` to copy last input/output to clipboard

[1.1.1]
- fix some selectors containing dash characters (`-`) being interpreted incorrectly

[1.1.0]
- add many new processors:
    ```
    --pretty, -p             pretty format html
    --slice, -[              take slice
    --re                     filter values by regex
    --repr, -r               represent output (e.g. show newline chars)
    -n                       take n-th element
    ```
- rework output and add coloring
- add prompt toolkit bottom toolbar, rprompt and vi_mode and related commands
- autocomplete improvements
- lots of bug fixes

[1.0.0]
- full rework and update with newest dependancies (request, parsel, click)
- rework commands to `--option` option format
- rework processors

[0.33]
- add history to embeded shell for ptpython
- add rolling support for config that will keep config up to date with changes

[0.32.1]
- hotfix missing brotli dependency

[0.32]
- add brotli econding decompression

[0.31]
- separate history for css and xpath selectors
- add "-h" option for supplying extra headers
- change default headers for something more obfuscated to avoid bot blocking

[0.30]
- add full configuration toml file, e.g. `~/.config/parsel.toml`
- rework cli: move processors as one tag,
- add inline flags e.g.: `h1::text +join`
- move `-view` command to `-open` and add `-view` command
- add Len processor and `+len` flag for returning output length

[0.26]
- add descriptions to commands and flags when -help command is called.
- add response object when reading from file.
- add cache requests
- move history to XDG compatible directory (e.g. .cache/parsel)
- rework commands and flags
- refactor structure

[0.25]
- add `join` processor flag for joining all values into one
- add `fetch` command for downloading other page without exiting interpreter
- add `view` command for opening the current page in default browser

[0.24]
- add `onlyfirst` processor flag for forcing first value despite everything
- add `absolute` processor flag for converting urls to absolute urls

[0.23]
- add compile options for css and xpath
- add `first` processor/flag that returns only the first element when only 1 result found.

[0.22]
- add embed options `--shell` and `--embed` for cli.

[0.2]
- add embed shell feature/command
- add small guide/description to readme.md

[0.1]
- initial version
