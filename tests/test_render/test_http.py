import json

from requests_cache import CachedResponse
from parselcli.render.http import HttpRenderer, CachedHttpRenderer


def test_cachehttp_render_basic_setup():
    with CachedHttpRenderer("http.cache") as render:
        url = "http://httpbin.org/headers"
        render.goto(url)
        assert render.response.url == url
        assert isinstance(render.response, CachedResponse)
        assert json.loads(render.content)


def test_cachehttp_render_switch_selector():
    with CachedHttpRenderer("http.cache") as render:
        # go to random url
        render.goto("http://httpbin.org/headers")
        # then test context switch
        url = "http://httpbin.org/html"
        render.goto(url)
        assert render.response.url == url
        assert render.selector.css("h1::text").get() == "Herman Melville - Moby-Dick"


def test_http_render_basic_setup():

    with HttpRenderer() as render:
        url = "http://httpbin.org/headers"
        render.goto(url)
        assert render.response.url == url
        assert json.loads(render.content)


def test_http_render_switch_selector():
    with HttpRenderer() as render:
        # go to random url
        render.goto("http://httpbin.org/headers")
        # then test context switch
        url = "http://httpbin.org/html"
        render.goto(url)
        assert render.response.url == url
        assert render.selector.css("h1::text").get() == "Herman Melville - Moby-Dick"
