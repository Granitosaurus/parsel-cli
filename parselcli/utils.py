import collections


def lazy_dict_merge(root, update):
    """
    this function merges two dictionaries lazily and recursively (supports nested dicts)

    Lazy means only missing keys will be updated,
    i.e. update['foo'] will only be copied to root if it doesn't have 'foo' already

    >>> lazy_dict_merge({'foo': '1'}, {'bar': '2'})
    {}
    >>> lazy_dict_merge({'foo': '1'}, {'bar': '2'})
    {}
    """
    result = {}
    for k, v in update.iteritems():
        if k not in root:
            result[k] = v
            continue
        if isinstance(root[k], dict) and isinstance(update[k], collections.Mapping):
            result[k] = lazy_dict_merge(root[k], update[k])
            continue
        result[k] = root[k]
    return result
