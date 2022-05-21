import curses
import logging
from typing import Optional

from ...external.actors import Actor, Message, Sig, ActorIO, create, send, DispatchError
from ...wcurses import stdscr


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
            case {'event': 'io', 'name': 'keypress', 'args': args}:
                match args:
                    case Key.ENTER:
                        CmdCache().push(CmdBuffer().get())
                        send('Display', Message(sig=Sig.PROMPT, args=False))
                        send(self.parent, {'event': 'command', 'name': 'parse', 'args': CmdBuffer().to_str()})
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
                    
                send('Display', Message(sig=Sig.PROMPT, args=CmdBuffer().serialize()))

    def init(self) -> None:
        send('Display', Message(sig=Sig.PROMPT, args=True))

    def terminate(self) -> None:
        send(self.parent, {'event': 'status', 'name': 'child-exit'})
        send('ActorSystem', Message(sig=Sig.EXIT))
        raise SystemExit


class InputIO(ActorIO):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.log_lvl = logging.WARNING

    def run(self) -> None:
        while 1:
            c = stdscr.getch()
            self.logger.info(f'Got new input c={c}')
            if c == -1: 
                continue
            send(self.parent, {'event': 'io', 'name': 'keypress', 'args': c})


class Input(Actor):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.log_lvl = logging.WARNING
        self.child: Optional[int] = None
        self.sidecar: int

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except DispatchError:
            return

        match msg:
            case {'event': 'status', 'name': 'child-exit'}:
                self.child = None

            case {'event': 'command', 'name': 'parse', 'args': args}:
                (recipient, response) = eval_cmd(args)
                send(recipient, response)

            case {'event': 'io', 'name': 'keypress', 'args': args} as msg if self.child is not None:                
                send(self.child, msg)

            case {'event': 'io', 'name': 'keypress', 'args': args}:
                match args:
                    case 0:
                        ...

                    case Key.COLON:
                        self.child = create(Prompt)
                        send(self.child, Message(sig=Sig.INIT))

                    case Key.q | Key.Q:
                        send('ActorSystem', Message(sig=Sig.SIGQUIT))

                    case Key.r | Key.R:
                        (recipient, response) = eval_cmd('refresh')
                        send(recipient, response)

                    case Key.p | Key.P:
                        (recipient, response) = eval_cmd('play')
                        send(recipient, response)

                    case Key.ALT_H:
                        send('MediaDispatcher', {'event': 'command', 'name': 'previous', 'args': None})

                    case Key.ALT_L:
                        send('MediaDispatcher', {'event': 'command', 'name': 'next', 'args': None})

                    case Key.SPACE:
                        send('MediaDispatcher', Message(sig=Sig.PLAY_PAUSE))

                    case Key.DOT:
                        (recipient, response) = eval_cmd('..')
                        send(recipient, response)

                    case (Key.H | Key.L | Key.J | Key.K) as p:
                        match p:
                            case Key.H:
                                arg = -5
                            case Key.L:
                                arg = 5
                            case Key.J:
                                arg = -10
                            case Key.K:
                                arg = 10
                            case _:
                                arg = None
                        send('MediaDispatcher', Message(sig=Sig.VOLUME_INC, args=arg))

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
                        (recipient, response) = eval_cmd(num_mapping[p])
                        send(recipient, response)

                    case _:
                        self.logger.warning(f'Unhandled key press: {args}')
            case _:
                self.logger.warning(f'Unprocessable msg={msg}')


    def init(self) -> None:
        self.sidecar = create(InputIO)
        send(self.sidecar, Message(sig=Sig.INIT))

    def terminate(self) -> None:
        send('ActorSystem', Message(sig=Sig.EXIT))
        raise SystemExit
