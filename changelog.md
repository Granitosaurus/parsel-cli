[0.31]
- separate history for css and xpath selectors

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
