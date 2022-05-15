import curses
from typing import Any
from signal import signal, SIGWINCH
import logging
import pickle

from ...utils import SingletonMeta, clamp
from ...external.actors import Actor, Message, Sig, actor_system, ActorGeneric
from . import helpers

from ...wcurses import stdscr, draw_popup


def resize_handler(signum, frame):
    curses.endwin()  # This could lead to crashes according to below comment
    stdscr.refresh()
    actor_system.send('Display', Message(sig=Sig.DRAW_SCREEN))


signal(SIGWINCH, resize_handler)

from dataclasses import dataclass

@dataclass(frozen=True)
class Msg:
    event: str
    name: str
    args: Any = None


class Display(Actor, metaclass=SingletonMeta):
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
        self.log_lvl = logging.ERROR

    def dispatch(self, sender: int, msg: Message) -> None:
        # super().dispatch(sender, msg)
        match msg:
            case Message(sig=Sig.CWD_GET, args=args):
                dir_list, files_list = args.get('dir_list'), args.get('files_list')
                self.files_buff = [dir_list, files_list]
                self.post(Message(sig=Sig.DRAW_SCREEN))

            case Message(sig=Sig.PROMPT, args=args) if isinstance(args, bool):
                # initialisation de la fenetre du prompt
                self.cmd_overlay = args
                if not self.cmd_overlay:
                    curses.curs_set(0)
                    self.cmd_buff = ('', 0)
                else:
                    ...
                self.post(Message(sig=Sig.DRAW_SCREEN))

            case Message(sig=Sig.PROMPT, args=args) if isinstance(args, tuple):
                self.cmd_buff = args
                self.post({'event': 'property-change', 'name': 'draw-cmd'})

            case {'event': 'property-change', 'name': 'draw-cmd'}:
            # case Msg(event='property-change', name='draw-cmd'):
                if self.cmd_overlay:
                    self.set_dims()
                    self.draw_cmd()
                    curses.doupdate()

            case Message(sig=Sig.MEDIA_META, args=args):
                k, v = [i for i in args.items()][0]
                self.media_meta.update({k: v})
                self.post({'event': 'property-change', 'name': 'draw-playback'})

            case {'event': 'property-change', 'name': 'draw-playback'}:
                if self.playback_overlay:
                    # helpers.set_dims(self)
                    # helpers.draw_playback(self)
                    self.set_dims()
                    self.draw_playback()
                    curses.doupdate()

            case Message(sig=Sig.DRAW_SCREEN):
                # self.post(self, {'type': 'publish'})
                self.set_dims()
                self.draw_files()
                self.draw_playback()
                self.draw_cmd()
                curses.doupdate()

            case Message(sig=Sig.PLAYBACK_OVERLAY, args=args):
                self.playback_overlay = not self.playback_overlay
                self.post(Message(sig=Sig.DRAW_SCREEN))

            case Message(sig=Sig.POPUP, args=args):
                draw_popup(args)

            case Message(sig=Sig.POISON, args=args):
                raise Exception(f'{msg!r}')

            # case Message(sig=Sig.AUDIT, args=rid):
            #     actor_system.send(sender, {'event': 'audit', 'rid': rid, 'data': self.introspect()})

            # case {'type': 'subscribe'}:
            #     self.subscribers.append(sender)

            # case {'type': 'publish'}:
            #     for a in self.subscribers:
            #         actor_system.send(a, {'type': 'publish', 'args': self.introspect()})

            case Message(sig=Sig.SIGQUIT):
                self.terminate()

            case _:
                self.logger.info(f'Can\'t handle msg={msg}')
                # raise SystemExit(f'{msg=}')

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
