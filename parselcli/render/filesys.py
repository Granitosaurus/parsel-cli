from pathlib import Path

from requests import Response

from parselcli.render import Renderer


class FileRenderer(Renderer):
    """Load HTML from local file system."""

    @property
    def content(self) -> str:
        return self.response.text

    def goto(self, url: str, **kwargs) -> Response:
        resp = Response()
        resp.url = url
        resp._content = Path(url).read_bytes()
        resp.status_code = 200
        self._response = resp
        return resp
