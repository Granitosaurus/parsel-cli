import shlex

from parselcli.parse import ToggleInputOptionParser


def test_ToggleInputOptionParser():
    o = ToggleInputOptionParser()
    o.add_option('-fetch', nargs=1, )
    o.add_option('-test', action='store_const', const=True)
    o.add_option('-default', nargs=-1, action='store')
    o.add_option('-fetch', nargs=1)
    o.add_option('-update', nargs=0)
    # test default behaviour
    text = '-fetch foo bar qux -test -default 1 -test'
    expected = (
        {'-fetch': 'foo', '-test': True, '-default': ('1',)},
        ['bar', 'qux'],
        ['-fetch', '-test', '-default', '-test'],
    )
    assert o.parse_args(shlex.split(text)) == expected
    # test added toggle behaviour
    o.add_option('+-strip', nargs=0)
    o.add_option('+-join', nargs=0, action='store_const', const=True)  # flag
    text = '+strip -strip +join'
    expected = (
        {'+strip': (), '-strip': (), '+join': True},
        [],
        ['+strip', '-strip', '+join'],
    )
    assert o.parse_args(shlex.split(text)) == expected
