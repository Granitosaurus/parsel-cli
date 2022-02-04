from parselcli.prompt.completer import CSS_COMPLETION, XPATH_COMPLETION


def find_attributes(sel, attr):
    """
    finds node attributes in a selector
    returns list of unique strings
    """
    classes = sel.xpath(f"//*/@{attr}").extract()
    classes = [c.strip() for cs in classes for c in cs.split()]
    return list(set(classes))


def find_nodes(sel):
    """
    Finds node names in a selector
    :returns list of unique strings
    """
    nodes = sel.xpath("//*")
    nodes = [n.xpath("name()").extract_first() for n in nodes]
    return list(set(nodes))


def get_css_completion(sel):
    """generates completion items for css from a selector"""
    node_names = find_nodes(sel)
    classes = ["." + c for c in find_attributes(sel, "class")]
    ids = ["#" + c for c in find_attributes(sel, "id")]
    return node_names + classes + ids + CSS_COMPLETION


def get_xpath_completion(sel):
    """generates completion items for xpath from a selector"""
    completion = find_nodes(sel)
    return completion + XPATH_COMPLETION
