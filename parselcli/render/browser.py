from parselcli.render import Renderer
from typing import Optional, Dict
from playwright.sync_api import sync_playwright
from playwright.sync_api._generated import Browser, Page, Playwright
from requests import Response


class PlaywrightRenderer(Renderer):
    def __init__(self, headers: Optional[Dict[str, str]] = None, **kwargs) -> None:
        super().__init__(headers=headers, **kwargs)
        self.pw: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.browser_kwargs = kwargs
    
    @property
    def content(self):
        return self.page.content()
    
    @property
    def response(self) -> Response:
        if not self._response:
            resp = Response()
            resp.url = self.page.url
            resp.status_code = 200
            resp._content = self.content.encode()
            self._response = resp
        return self._response

    def open(self):
        self._pw_ctx = sync_playwright()
        self.pw = self._pw_ctx.start()
        self.browser = self.pw.chromium.launch(headless=False, **self.browser_kwargs)
        self.page = self.browser.new_page()

    def close(self):
        self._pw_ctx.__exit__()

    def goto(self, url, wait_for_load="domcontentloaded") -> Response:
        self.page.goto(url)
        self.page.wait_for_load_state(wait_for_load)
        self._response = None
        self._sel = None
