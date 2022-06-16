import webbrowser
from functools import partial
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Callable, Dict

import pyperclip
from click import echo
from loguru import logger as log
from parselcli.embed import embed_auto
from parselcli.render import Renderer

if TYPE_CHECKING:
    from parselcli.prompt import Prompter

echo = partial(echo, err=True)


class PromptCommands:
    def __init__(self, prompt: "Prompter") -> None:
        self.prompt = prompt
        self.renderer: Renderer = self.prompt.renderer

    @property
    def commands(self) -> Dict[str, Callable]:
        """commands prompter support"""
        return {name.split("cmd_")[1]: getattr(self, name) for name in dir(self) if name.startswith("cmd_")}

    def cmd_fetch(self, text):
        """switch current session to different url by making a new request"""
        url = text.strip()
        echo(f"requesting: {url}")
        self.prompt.renderer.goto(url)
        self.prompt.create_completers(self.renderer.selector)

    def cmd_open(self):
        """open current response url in browser"""
        webbrowser.open_new_tab(self.renderer.response.url)

    def cmd_view(self):
        """open current response data in browser"""
        with NamedTemporaryFile("w", encoding=self.renderer.response.encoding, delete=False, suffix=".html") as file:
            file.write(self.renderer.content)
        webbrowser.open_new_tab(f"file://{file.name}")

    def cmd_help(self):
        """print usage help"""
        echo("Commands:")
        for opt in self.prompt.options_commands:
            echo(f"{', '.join(opt.opts + opt.secondary_opts):<25}{opt.help}")
        echo("Processors:")
        for opt in self.prompt.options_processors:
            echo(f"{', '.join(opt.opts + opt.secondary_opts):<25}{opt.help}")

    def cmd_info(self):
        """print info about current session"""
        if self.renderer.response is None:
            echo("No response object attached")
        else:
            echo(f"{self.renderer.response.status_code} {self.renderer.response.url}")
        echo(f"Enabled processors: {self.prompt.active_processors}")

    def cmd_embed(self):
        """Open current shell in embed repl"""
        request = self.renderer.response.request if self.renderer.response is not None else None
        namespace = {
            "renderer": self.renderer,
            "r": self.renderer,
            "request": request,
            "req": request,
            "_prompter": self.prompt,
            "page": getattr(self.renderer, "page", None),
            "p": getattr(self.renderer, "page", None),
            "outs": self.prompt.output_history,
            "out": self.prompt.output_history[-1] if self.prompt.output_history else None,
            "in_css": list(self.prompt._history_file_css.load_history_strings()),
            "in_xpath": list(self.prompt._history_file_xpath.load_history_strings()),
        }
        log.debug(f"embedding {self.prompt.preferred_embed_shell} shell")
        embed_auto(
            namespace,
            preferred=self.prompt.preferred_embed_shell,
            history_filename=self.prompt._history_file_embed,
        )

    def cmd_css(self):
        """switch current session to css selectors"""
        echo("switched to css")
        self.prompt.mode = "css"

    def cmd_xpath(self):
        """switch current session to xpath selectors"""
        echo("switched to xpath")
        self.prompt.mode = "xpath"

    def cmd_reset(self):
        """resets current processors"""
        self.prompt.active_processors = []
        echo(f"active processors: {self.prompt.active_processors}")

    def cmd_vi(self):
        """toggles vi mode of input"""
        self.prompt.use_vi_mode = not self.prompt.use_vi_mode
        echo(f"vi mode turned {'ON' if self.prompt.use_vi_mode else 'OFF'}")

    def cmd_clipin(self):
        """copy last input to clipboard"""
        value = self.prompt.prompt_history.load_history_strings()
        next(value)  # need to skip first history element as it's "--clipin" command itself
        value = next(value)
        pyperclip.copy(repr(value))
        echo(f"copied \"{value if len(value)<100 else value[:100] + '<...>'}\" to clipboard")

    def cmd_clipout(self):
        """copy last output to clipboard"""
        value = self.prompt.output_history[0]
        pyperclip.copy(repr(value))
        echo(f"copied {value if len(value)<100 else value[:100] + '<...>'} to clipboard")
