from parselcli.utils import lazy_dict_merge


def test_lazy_dict_merge():
    expected = [
        (
            {'foo': '1'}, {'bar': '2'},
            {'foo': '1', 'bar': '2'}
        ),
        # (
        #     {},
        #     {}
        # ),
    ]

    for arg1, arg2, exp in expected:
        assert lazy_dict_merge(arg1, arg2) == expected
