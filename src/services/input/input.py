import curses
import logging
from typing import Optional, Any
import select
import sys

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
                        send(self.pid, Message(sig=Sig.EXIT))
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
        send('Display', Event(type='io', name='prompt', args=True))

    def terminate(self) -> None:
        send(self.parent, Event(type='status', name='child-exit'))
        send('ActorSystem', Message(sig=Sig.EXIT))
        raise SystemExit


class Input(Actor):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.log_lvl = logging.WARNING
        self.child: Optional[int] = None

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except DispatchError:
            return

        arg: Any
        match msg:
            case Event(type='status', name='child-exit'):
                # hanling in super().dispatch
                self.child = None

            case Event(type='io', name='prompt', args=args):
                send(*eval_cmd(args))

            case Event(type='io', name='keypress', args=args) as msg if self.child is not None:
                send(self.child, msg)

            case Event(type='io', name='keypress', args=args):
                match args:
                    case 0:
                        ...

                    case Key.COLON:
                        self.child = create(Prompt)
                        send(to=self.child, what=Message(sig=Sig.INIT))

                    case Key.q | Key.Q:
                        send(to='ActorSystem', what=Message(sig=Sig.SIGQUIT))

                    case Key.r | Key.R:
                        send(*eval_cmd('refresh'))

                    case Key.p | Key.P:
                        send(*eval_cmd('play'))

                    case Key.ALT_H:
                        send('MediaDispatcher', {'event': 'command', 'name': 'previous', 'args': None})

                    case Key.ALT_L:
                        send('MediaDispatcher', {'event': 'command', 'name': 'next', 'args': None})

                    case Key.SPACE:
                        send('MediaDispatcher', Message(sig=Sig.PLAY_PAUSE))

                    case Key.DOT:
                        send(*eval_cmd('..'))

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
                        send('MediaDispatcher', Message(sig=Sig.VOLUME, args=arg))

                    case (Key.d | Key.D):
                        send('Display', Message(sig=Sig.PLAYBACK_OVERLAY))

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
                        send('MediaDispatcher', Message(sig=Sig.SEEK, args=arg))

                    case p if p in num_mapping:
                        send(*eval_cmd(num_mapping[p]))

                    case _:
                        self.logger.warning(f'Unhandled key press: {args}')
            case _:
                raise DispatchError(f'Unprocessable msg={msg}')


    def terminate(self) -> None:
        if self.child is not None:
            send(self.child, Message(Sig.EXIT))
        send('ActorSystem', Message(sig=Sig.EXIT))
        raise SystemExit
