"""
Utility functions used by parsecli
"""
from copy import deepcopy


def lazy_dict_merge(root, update):
    """
    this function merges two dictionaries lazily and recursively (supports nested dicts)

    Lazy means only missing keys will be updated,
    i.e. update['foo'] will only be copied to root if it doesn't have 'foo' already

    >>> lazy_dict_merge({'foo': '1'}, {'bar': '2'})
    {'foo': '1', 'bar': '2'}
    >>> lazy_dict_merge({'foo': '1'}, {'bar': '2', 'foo': '3'})
    {'foo': '1', 'bar': '2'}
    """
    result = deepcopy(root)
    for key, value in update.items():
        if key not in root:
            result[key] = value
            continue
        if isinstance(root[key], dict) and isinstance(update[key], dict):
            result[key] = lazy_dict_merge(root[key], update[key])
            continue
        result[key] = root[key]
    return result
