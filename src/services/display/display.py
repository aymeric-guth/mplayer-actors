import curses
from typing import Any
from signal import signal, SIGWINCH
import logging

from ...utils import SingletonMeta, clamp
from ...external.actors import Actor, Message, Sig, send, DispatchError, create, MsgCtx, forward, Event, Request, Response
from . import helpers
from .wcurses import Curses

from ...wcurses import stdscr, draw_popup


def resize_handler(signum, frame):
    curses.endwin()  # This could lead to crashes according to below comment
    stdscr.refresh()
    send('Display', Message(sig=Sig.DRAW_SCREEN))


signal(SIGWINCH, resize_handler)



class Display(Actor):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.files_overlay = 1
        self.files_dims: tuple[int, int, int, int]
        self.files_buff: list[Any] = []
        self.playback_overlay = 1
        self.playback_dims: tuple[int, int, int, int]
        self.media_meta: dict[str, Any] = {}
        self.cmd_overlay = 0
        self.cmd_dims: tuple[int, int, int, int]
        self.cmd_buff: tuple[str, int] = ('', 0)
        self._cur = 0

        self.set_dims = lambda: helpers.set_dims(self)
        self.draw_cmd = lambda: helpers.draw_cmd(self)
        self.draw_files = lambda: helpers.draw_files(self)
        self.draw_playback = lambda: helpers.draw_playback(self)
        self.child: int
        self.log_lvl = logging.ERROR

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except DispatchError:
            return

        match msg:
            case Message(sig=Sig.CWD_GET, args=args):
                dir_list, files_list = args.get('dir_list'), args.get('files_list')
                self.files_buff = [dir_list, files_list]
                # send(self.pid, Request(type='render', name='draw'))
                send(self.pid, Message(sig=Sig.DRAW_SCREEN))

            case Event(type='io', name='prompt', args=args) if isinstance(args, bool):
                # initialisation de la fenetre du prompt
                self.cmd_overlay = args
                if not self.cmd_overlay:
                    curses.curs_set(0)
                    self.cmd_buff = ('', 0)
                else:
                    ...
                send(self.pid, Message(sig=Sig.DRAW_SCREEN))

            case Event(type='io', name='prompt', args=args) if isinstance(args, tuple):
                self.cmd_buff = args
                if self.cmd_overlay:
                    self.set_dims()
                    send(self.child, Request(type='render', name='cmd', args=(self.cmd_dims, self.cmd_buff)))

                # self.cmd_buff = args
                # if self.cmd_overlay:
                #     self.set_dims()
                #     self.draw_cmd()
                #     curses.doupdate()

            case Message(sig=Sig.MEDIA_META, args=args):
                k, v = [i for i in args.items()][0]
                self.media_meta.update({k: v})
                send(self.pid, {'event': 'property-change', 'name': 'draw-playback'})

            case {'event': 'property-change', 'name': 'draw-playback'}:
                if self.playback_overlay:
                    # helpers.set_dims(self)
                    # helpers.draw_playback(self)
                    self.set_dims()
                    self.draw_playback()
                    curses.doupdate()

            case Message(sig=Sig.DRAW_SCREEN):
                self.set_dims()
                self.draw_files()
                self.draw_playback()
                self.draw_cmd()               
                curses.doupdate()

            case Message(sig=Sig.PLAYBACK_OVERLAY, args=args):
                self.playback_overlay = not self.playback_overlay
                send(self.pid, Message(sig=Sig.DRAW_SCREEN))

            case Message(sig=Sig.POPUP, args=args):
                draw_popup(args)

            case _:
                raise DispatchError

    def dispatch_handler(self, sender: int, message: Message|dict[str, Any]) -> None:
        self.logger.error(f'Reached dispatch_handler msg={message!r}')
        return forward(sender, self.child, message)

    def introspect(self) -> dict[Any, Any]:
        return {
            'actor': repr(self),
            'log_lvl': self.log_lvl,
            'data': {
                'files_overlay': self.files_overlay,
                'playback_overlay': self.playback_overlay,
                'cmd_overlay': self.cmd_overlay,
                'cmd_buff': self.cmd_buff.copy(),
                'files_buff': self.files_buff.copy(),
                'media_meta': self.media_meta.copy(),
            }
        }.copy()

    @property
    def cur(self) -> int:
        return self._cur

    @cur.setter
    def cur(self, value: int) -> None:
        self._cur = value

    def init(self) -> None:
        self.child = create(Curses)
        send(self.child, Message(sig=Sig.INIT))
