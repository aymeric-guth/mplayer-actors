import curses
from typing import Any
from signal import signal, SIGWINCH
import logging

from ...utils import SingletonMeta, clamp
from ...external.actors import Actor, Message, Sig, send, DispatchError, create, MsgCtx, forward, Event, Request, Response
from .wcurses import Curses


def resize_handler(signum, frame):
    send(to='Display', what=Event(type='signal', name='resize'))


signal(SIGWINCH, resize_handler)



class Display(Actor):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self._files_overlay = 1
        self.files_dims: tuple[int, int, int, int]
        self.files_buff: list[Any] = [[], []]
        self._playback_overlay = 1
        self.playback_dims: tuple[int, int, int, int]
        self.media_meta: dict[str, Any] = {}
        self._cmd_overlay = 0
        self.cmd_dims: tuple[int, int, int, int]
        self.cmd_buff: tuple[str, int] = ('', 0)

        self.log_lvl = logging.ERROR

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except DispatchError:
            return
        # state-change (overlay on/off)
        #   -> render global
        # data-change (new cwd, typing in prompt, media-playback update)
        #   -> render de l'élément modifié

        match msg:
            case Event(type='io', name='prompt', args=args) if isinstance(args, bool):
                # initialisation de la fenetre du prompt
                self.cmd_overlay = args
                if not self.cmd_overlay:
                    self.cmd_buff = ('', 0)
                send(to=self.pid, what=Event(type='io', name='resize'))

            case Event(type='io', name='prompt', args=args) if isinstance(args, tuple):
                self.cmd_buff = args
                if self.cmd_overlay:
                    send(self.child, Request(type='render', name='cmd', args=self.cmd_buff))

            case Event(type='player', name='property-change', args=args):
                k, v = [i for i in args.items()][0]
                self.media_meta.update({k: v})
                if self.playback_overlay:
                    send(self.child, Request(type='render', name='playback', args=self.media_meta.copy()))

            case Event(type='files', name='cwd-change', args=args):
                dir_list, files_list = args.get('dir_list'), args.get('files_list')
                self.files_buff = [dir_list, files_list]
                if self.files_overlay:
                    send(self.child, Request(type='render', name='files', args=[dir_list, files_list]))

            case Event(type='io', name='resize'):
                (dir_list, files_list) = self.files_buff
                if self.files_overlay:
                    send(self.child, Request(type='render', name='files', args=[dir_list, files_list]))
                if self.playback_overlay:
                    send(self.child, Request(type='render', name='playback', args=self.media_meta.copy()))
                if self.cmd_overlay:
                    send(self.child, Request(type='render', name='cmd', args=self.cmd_buff))

            case Event(type='signal', name='resize') as msg:
                send(to=self.child, what=msg)

            case Event(type='keypress', name='playback-toggle'):
                self.playback_overlay = not self.playback_overlay
                send(to=self.pid, what=Event(type='io', name='resize'))

            case Message(sig=Sig.POPUP, args=args):
                ...
                # draw_popup(args)

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
    def files_overlay(self) -> int:
        return self._files_overlay

    @files_overlay.setter
    def files_overlay(self, value: int) -> None:
        self._files_overlay = value
        send(to=self.child, what=Event(type='state-change', name='files', args=self._files_overlay))

    @property
    def playback_overlay(self) -> int:
        return self._playback_overlay

    @playback_overlay.setter
    def playback_overlay(self, value: int) -> None:
        self._playback_overlay = value
        send(to=self.child, what=Event(type='state-change', name='playback', args=self._playback_overlay))

    @property
    def cmd_overlay(self) -> int:
        return self._cmd_overlay

    @cmd_overlay.setter
    def cmd_overlay(self, value: int) -> None:
        self._cmd_overlay = value
        send(to=self.child, what=Event(type='state-change', name='cmd', args=self._cmd_overlay))

    def init(self) -> None:
        create(Curses)

    def terminate(self) -> None:
        send(to='ActorSystem', what=Message(sig=Sig.EXIT))
        send(to=self.child, what=Message(sig=Sig.EXIT))
        raise SystemExit
