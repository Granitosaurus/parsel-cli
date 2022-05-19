from parselcli.render import Renderer
from typing import Optional, Dict

try:
    from playwright.sync_api import sync_playwright
    from playwright.sync_api._generated import Browser, Page, Playwright

    PW_SUPPORTED = True
except ImportError:
    PW_SUPPORTED = False

from requests import Response
from loguru import logger as log


class PlaywrightRenderer(Renderer):
    def __init__(self, headers: Optional[Dict[str, str]] = None, **kwargs) -> None:
        if not PW_SUPPORTED:
            raise ImportError(
                "to use Playwright rendering Playwright is required; use `pip install parsel[browser]` "
                "instead of `pip install parsel`"
            )
        super().__init__(headers=headers, **kwargs)
        self.pw: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.browser_kwargs = kwargs.get("browser_kwargs", {})

    @property
    def content(self):
        return self.page.content()

    @property
    def response(self) -> Response:
        resp = Response()
        resp.url = self.page.url
        resp.status_code = 200
        resp._content = self.content.encode()
        # TODO this can be more sophisticated
        return resp
        # self._response = resp
        # return response

    def open(self):
        self._pw_ctx = sync_playwright()
        self.pw = self._pw_ctx.start()
        log.debug(f"launching chromium browser with kwargs: {self.browser_kwargs}")
        self.browser = self.pw.chromium.launch(**self.browser_kwargs)
        self.page = self.browser.new_page()

    def close(self):
        self._pw_ctx.__exit__()

    def goto(self, url, wait_for_load="domcontentloaded") -> Response:
        self.page.goto(url)
        self.page.wait_for_load_state(wait_for_load)
        # self._response = None
        # self._sel = None
