# parsel-cli Usage Examples

This document contains examples of common `parsel-cli` usage patterns.

Format Legend:

* Lines prefixed with `#` are instructional comments
* Lines prefixed with `>` are parsel inputs
* Lines prefixed with `>>>` are embed shell inputs
* Unmarked lines are either parsel or embed shell outputs

## Use --embed to further inspect output

Parsel CLI tracks output for the current session. This feature can be used with `--embed` command to further inspect output in python shell.

For example we want to calculate total points on hacker news front-page:

```
$ parsel https://news.ycombinator.com/
# First we figure out css selector for points:
> tr .score::text
[
    '336 points',
    '85 points',
    '34 points',
    '152 points',
    '569 points',
    '38 points',
    ...
]

# once we found a working selector. We can further inspect the output in the interactive shell
> --embed
# `out` variable gets populated with last output
>>> out
['336 points', '85 points', '34 points', '152 points', '569 points', '38 points', '350 points', '83 points', '88 points', '389 points', '14 points', '111 points', '111 points', '7 points', '15 points', '64 points', '71 points', '214 points', '76 points', '23 points', '72 points', '83 points', '285 points', '58 points', '43 points', '59 points', '19 points', '106 points', '64 points']
# now we can run python
>>> sum(int(x.split()[0]) for x in out)
3619
```

