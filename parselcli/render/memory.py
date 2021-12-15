from parselcli.render import Renderer
from requests import Response


class MemoryRenderer(Renderer):
    def goto(self, url, **kwargs) -> Response:
        resp = Response()
        resp.url = url
        resp._content = kwargs["content"].encode()
        resp.status_code = 200
        self._response = resp
        return resp
