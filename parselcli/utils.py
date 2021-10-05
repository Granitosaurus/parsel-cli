"""
Utility functions used by parselcli
"""
# pylint: disable=I1101
from copy import deepcopy
from lxml import etree


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


def prettify_html_lxml(element):
    """Prettify html by using lxml pretty_print functionality"""
    parser = etree.HTMLParser(remove_blank_text=True)
    as_node = etree.fromstring(element, parser)[0]  # remove <html> tag
    result = etree.tostring(as_node, encoding="unicode", pretty_print=True)
    # remove <body> wrapper
    result = result.split("<body>", 1)[1].rsplit("</body>", 1)[0].strip()
    result, *tail = result.rsplit("\n", 1)
    if tail:
        result += "\n" + tail[0].strip()
    return result
