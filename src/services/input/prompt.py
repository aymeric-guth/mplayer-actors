import curses
import logging

from actors import (
    Actor,
    Message,
    Sig,
    send,
    Event,
    SystemMessage,
)

from .constants import Key
from .helpers import CmdCache, CmdBuffer


class Prompt(Actor):
    def __init__(self, pid: int, parent: int, name="", key: int = 0, **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.log_lvl = logging.ERROR
        self.key = key

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except SystemMessage:
            return

        match msg:
            case Event(type="io", name="keypress", args=args):
                match args:
                    case Key.ENTER:
                        CmdCache().push(CmdBuffer().get())
                        send(
                            to="Display",
                            what=Event(type="io", name="prompt", args=False),
                        )
                        send(
                            to=self.parent,
                            what=Event(
                                type="io",
                                name="prompt",
                                args=(self.key, CmdBuffer().to_str()),
                            ),
                        )
                        CmdBuffer().clear()
                        send(to=self.pid, what=Message(sig=Sig.EXIT))
                        return

                    case Key.BACKSPACE:
                        CmdBuffer().delete()

                    case Key.DELETE:
                        CmdBuffer().delete(1)

                    case curses.KEY_UP:
                        CmdBuffer().init(CmdCache().prev())

                    case curses.KEY_DOWN:
                        CmdBuffer().init(CmdCache().next())

                    case curses.KEY_LEFT:
                        CmdBuffer().mov()

                    case curses.KEY_RIGHT:
                        CmdBuffer().mov(1)

                    case _:
                        CmdBuffer().insert(chr(args))
                        if self.key == Key.QUERY:
                            send(
                                to=self.parent,
                                what=Event(
                                    type="io",
                                    name="prompt",
                                    args=(self.key, CmdBuffer().to_str()),
                                ),
                            )

                send(
                    to="Display",
                    what=Event(type="io", name="prompt", args=CmdBuffer().serialize()),
                )

    def init(self) -> None:
        send(to="Display", what=Event(type="io", name="prompt", args=True))
