import json
from parselcli.render.browser import PlaywrightRenderer


def test_browser_render_basic_setup():
    with PlaywrightRenderer() as render:
        url = "http://httpbin.org/headers"
        render.goto(url)
        assert render.response.url == url
        assert json.loads(render.selector.css("::text").get())
        # test context switch
        url = "http://httpbin.org/html"
        render.goto(url)
        assert render.response.url == url
        assert render.selector.css("h1::text").get() == "Herman Melville - Moby-Dick"