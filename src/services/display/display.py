import curses
from typing import Any
from signal import signal, SIGWINCH
import logging
import time

from ...utils import SingletonMeta, clamp
from ...external.actors import Actor, Message, Sig, send, DispatchError, create, MsgCtx, forward, Event, Request, Response, ActorSystem, SystemMessage
from .wcurses import Curses
from ...external.actors.utils import Observable


# signal(SIGWINCH, lambda signum, frame: send(to='Display', what=Event(type='signal', name='resize')))


class Display(Actor):
    files_overlay = Observable(setter=lambda x: 1 if x else 0)
    cmd_overlay = Observable(setter=lambda x: 1 if x else 0)
    playback_overlay = Observable(setter=lambda x: 1 if x else 0)
    files_buff = Observable()
    cmd_buff = Observable()

    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.files_overlay = 1
        self.files_dims: tuple[int, int, int, int]
        self.files_buff = [[], []]
        self.playback_overlay = 1
        self.playback_dims: tuple[int, int, int, int]
        self.media_meta: dict[str, Any] = {}
        self.cmd_overlay = 0
        self.cmd_dims: tuple[int, int, int, int]
        self.cmd_buff = ('', 0)
        self.log_lvl = logging.ERROR
        # self.log_lvl = logging.INFO
        self.events = {'property-change',}
        self.subs = [
            ('MediaDispatcher', 'current-item'),
            ('MediaDispatcher', 'playlist-pos'),
            ('MediaDispatcher', 'playback-mode'),

            ('MediaDispatcher', 'volume'),
            ('MediaDispatcher', 'time-pos'),
            ('MediaDispatcher', 'duration'),
            ('MediaDispatcher', 'player-state'),
        ]
    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except SystemMessage:
            return
        # state-change (overlay on/off)
        #   -> render global
        # data-change (new cwd, typing in prompt, media-playback update)
        #   -> render de l'élément modifié

        # if isinstance(msg, Event) and msg.type in self.events:
        #     self.logger.log(sender=repr(ActorSystem().get_actor(sender)), receiver=repr(self), msg=repr(msg))

        match msg:
            case Event(type='io', name='prompt', args=args) if isinstance(args, bool):
                # initialisation de la fenetre du prompt
                self.cmd_overlay = args
                if not self.cmd_overlay:
                    self.cmd_buff = ('', 0)
                send(to=self.pid, what=Event(type='io', name='resize'))

            case Event(type='io', name='prompt', args=args) if isinstance(args, tuple):
                self.cmd_buff = args

            case Event(type='property-change', name=name, args=args):
                self.media_meta.update({name: args})
                if self.playback_overlay:
                    send(self.child, Request(type='render', name='playback', args=self.media_meta.copy()))

            case Event(type='files', name='cwd-change', args=args):
                dir_list, files_list = args.get('dir_list'), args.get('files_list')
                self.files_buff = [dir_list, files_list]

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

            case Event(type='error', name='bad-cmd', args=args):
                send(to=self.child, what=Request(type='render', name='popup', args=args))

            case _:
                ...
                # raise DispatchError

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


    def init(self) -> None:
        create(Curses)
        for actor, event in self.subs:
            send(to=actor, what=Message(sig=Sig.SUBSCRIBE, args=event))

    def terminate(self) -> None:
        for actor, event in self.subs:
            send(to=actor, what=Message(sig=Sig.UNSUBSCRIBE, args=event))
        send(to=self.child, what=Message(sig=Sig.EXIT))
        raise SystemExit
