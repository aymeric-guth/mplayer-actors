import curses
import logging
from typing import Optional, Any
import select
import sys
import time

from ...external.actors import Actor, Message, Sig, ActorIO, create, send, DispatchError, Event, Request, Response
# from ...wcurses import stdscr


from .constants import num_mapping, Key
from .helpers import CmdCache, eval_cmd, CmdBuffer
from ...utils import SingletonMeta


class Prompt(Actor):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.log_lvl = logging.ERROR

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except DispatchError:
            return

        match msg:
            case Event(type='io', name='keypress', args=args):
                match args:
                    case Key.ENTER:
                        CmdCache().push(CmdBuffer().get())
                        send(to='Display', what=Event(type='io', name='prompt', args=False))
                        send(to=self.parent, what=Event(type='io', name='prompt', args=CmdBuffer().to_str()))
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
                send(to='Display', what=Event(type='io', name='prompt', args=CmdBuffer().serialize()))

    def init(self) -> None:
        send(to='Display', what=Event(type='io', name='prompt', args=True))


class Input(Actor):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.log_lvl = logging.WARNING

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except DispatchError:
            return

        arg: Any
        match msg:
            case Event(type='io', name='prompt', args=args):
                (actor, message) = eval_cmd(args)
                send(to=actor, what=message)

            case Event(type='io', name='keypress', args=args) as msg if self.child:
                send(self.child, msg)

            case Event(type='io', name='keypress', args=args):
                match args:
                    case 0:
                        ...

                    case Key.COLON:
                        create(Prompt)

                    case Key.q | Key.Q:
                        send(to='ActorSystem', what=Message(sig=Sig.SIGQUIT))

                    case Key.r | Key.R:
                        (actor, message) = eval_cmd('refresh')
                        send(to=actor, what=message)

                    case Key.p | Key.P:
                        (actor, message) = eval_cmd('play')
                        send(to=actor, what=message)

                    case Key.ALT_H:
                        send('MediaDispatcher', Request(type='player', name='play-previous'))
                        # send('MediaDispatcher', {'event': 'command', 'name': 'previous', 'args': None})

                    case Key.ALT_L:
                        send('MediaDispatcher', Request(type='player', name='play-next'))
                        # send('MediaDispatcher', {'event': 'command', 'name': 'next', 'args': None})

                    case Key.SPACE:
                        send('MediaDispatcher', Message(sig=Sig.PLAY_PAUSE))

                    case Key.DOT:
                        (actor, message) = eval_cmd('..')
                        send(to=actor, what=message)

                    case (Key.H | Key.L | Key.J | Key.K) as p:
                        match p:
                            case Key.H:
                                arg = '-5'
                            case Key.L:
                                arg = '+5'
                            case Key.J:
                                arg = '-10'
                            case Key.K:
                                arg = '+10'
                            case _:
                                arg = '0'
                        send(to='MediaDispatcher', what=Message(sig=Sig.VOLUME, args=arg))

                    case (Key.d | Key.D):
                        send(to='Display', what=Event(type='keypress', name='playback-toggle'))

                    case (curses.KEY_LEFT | Key.h | curses.KEY_RIGHT | Key.l | curses.KEY_UP | Key.k | curses.KEY_DOWN | Key.j) as p:
                        match p:
                            case curses.KEY_LEFT | Key.h:
                                arg = -5
                            case curses.KEY_RIGHT | Key.l:
                                arg = 5
                            case curses.KEY_UP | Key.k:
                                arg = 60
                            case curses.KEY_DOWN | Key.j:
                                arg = -60
                            case _:
                                arg = None
                        send(to='MediaDispatcher', what=Message(sig=Sig.SEEK, args=arg))

                    case p if p in num_mapping:
                        (actor, message) = eval_cmd(num_mapping[p])
                        send(to=actor, what=message)

                    case _:
                        self.logger.warning(f'Unhandled key press: {args}')

            case _:
                raise DispatchError(f'Unprocessable msg={msg}')


    def terminate(self) -> None:
        if self.child:
            send(to=self.child, what=Message(Sig.EXIT))
        # while self.child:
        #     time.sleep(0.1)
        raise SystemExit
