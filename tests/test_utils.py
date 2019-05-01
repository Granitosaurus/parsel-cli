from parselcli.utils import lazy_dict_merge


def test_lazy_dict_merge():
    expected = [
        (  # two different ones
            {'foo': '1'}, {'bar': '2'},
            {'foo': '1', 'bar': '2'}
        ),
        (  # existing key
            {'foo': '1'}, {'bar': '2', 'foo': '3'},
            {'foo': '1', 'bar': '2'}
        ),
        (  # existing key
            {'nested': {'foo': '1'}}, {'nested': {'bar': '2'}},
            {'nested': {'foo': '1', 'bar': '2'}}
        ),
        (  # combined
            {'nested': {'foo': '1'}}, {'nested': {'bar': '2'}, 'extra': '1'},
            {'nested': {'foo': '1', 'bar': '2'}, 'extra': '1'}
        ),
    ]

    for arg1, arg2, exp in expected:
        assert exp == lazy_dict_merge(arg1, arg2)
