from requests.sessions import Session
from requests_cache import CachedSession, ExpirationTime
from parselcli.render import Renderer
from typing import Optional, Dict


class HttpRenderer(Renderer):
    def __init__(self, headers: Optional[Dict[str, str]] = None, **kwargs) -> None:
        super().__init__(headers, **kwargs)
        self.session: Optional[Session] = None
        self.headers = headers or {}

    @property
    def content(self):
        return self.response.text

    def open(self):
        self.session = Session()
        self.session.headers.update(**self.headers)

    def goto(self, url: str):
        self._response = self.session.get(url)
        self._sel = None


class CachedHttpRenderer(HttpRenderer):
    def __init__(
        self, cache_file: str, cache_expire: ExpirationTime = -1, headers: Optional[Dict[str, str]] = None, **kwargs
    ) -> None:
        super().__init__(headers, **kwargs)
        self.cache_file = cache_file
        self.cache_expire = cache_expire

    def open(self):
        self.session = CachedSession(self.cache_file, expire_after=self.cache_expire)
