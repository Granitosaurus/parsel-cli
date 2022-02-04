from parsel import Selector
from typing import Optional, Dict
from requests import Response
from parselcli.prompt.completer import CSS_COMPLETION, XPATH_COMPLETION, MiddleWordCompleter
from loguru import logger as log


class Renderer:
    """http render backend"""

    def __init__(self, headers: Optional[Dict[str, str]] = None, **kwargs) -> None:
        self._response: Optional[Response] = None
        self.headers = headers
        self.kwargs = kwargs

    @property
    def response(self) -> Response:
        return self._response

    @property
    def content(self) -> str:
        return self.response.text

    @property
    def selector(self) -> Selector:
        return Selector(text=self.content)

    sel = selector

    def goto(self, url, **kwargs) -> Response:
        return

    def open(self):
        pass

    def close(self):
        pass

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()
