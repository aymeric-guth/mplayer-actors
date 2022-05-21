import curses
import logging
from typing import Optional

from ...external.actors import Actor, Message, Sig, actor_system, ActorIO, create
from ...wcurses import stdscr


from .constants import num_mapping, Key
from .helpers import CmdCache, eval_cmd, CmdBuffer
from ...utils import SingletonMeta


class Prompt(Actor):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.log_lvl = logging.ERROR

    def dispatch(self, sender: int, msg: Message) -> None:
        super().dispatch(sender, msg)
        match msg:
            case {'event': 'io', 'name': 'keypress', 'args': args}:
                match args:
                    case Key.ENTER:
                        CmdCache().push(CmdBuffer().get())
                        actor_system.send('Display', Message(sig=Sig.PROMPT, args=False))
                        actor_system.send(self.parent, {'event': 'command', 'name': 'parse', 'args': CmdBuffer().to_str()})
                        CmdBuffer().clear()
                        self.post(Message(sig=Sig.EXIT))
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
                    
                actor_system.send('Display', Message(sig=Sig.PROMPT, args=CmdBuffer().serialize()))

    def init(self) -> None:
        actor_system.send('Display', Message(sig=Sig.PROMPT, args=True))

    def terminate(self) -> None:
        actor_system.send(self.parent, {'event': 'status', 'name': 'child-exit'})
        actor_system.send('ActorSystem', Message(sig=Sig.EXIT))
        raise SystemExit


class InputIO(ActorIO, metaclass=SingletonMeta):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.log_lvl = logging.WARNING

    def run(self) -> None:
        while 1:
            c = stdscr.getch()
            self.logger.info(f'Got new input c={c}')
            if c == -1: 
                continue
            self.handler({'event': 'io', 'name': 'keypress', 'args': c})


class Input(Actor, metaclass=SingletonMeta):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.log_lvl = logging.WARNING
        self.child: Optional[int] = None
        self.sidecar: int
        self.post(Message(sig=Sig.INIT))

    def dispatch(self, sender: int, msg: Message) -> None:
        super().dispatch(sender, msg)
        match msg:
            case {'event': 'status', 'name': 'child-exit'}:
                self.child = None

            case {'event': 'command', 'name': 'parse', 'args': args}:
                (recipient, response) = eval_cmd(args)
                actor_system.send(recipient, response)

            case {'event': 'io', 'name': 'keypress', 'args': args} as msg if self.child is not None:                
                actor_system.send(self.child, msg)

            case {'event': 'io', 'name': 'keypress', 'args': args}:
                match args:
                    case 0:
                        ...

                    case Key.COLON:
                        # self.child = actor_system.create_actor(Prompt)
                        self.child = create(Prompt)

                    case Key.q | Key.Q:
                        actor_system.send('ActorSystem', Message(sig=Sig.SIGQUIT))

                    case Key.r | Key.R:
                        (recipient, response) = eval_cmd('refresh')
                        actor_system.send(recipient, response)

                    case Key.p | Key.P:
                        (recipient, response) = eval_cmd('play')
                        actor_system.send(recipient, response)

                    case Key.ALT_H:
                        actor_system.send('MediaDispatcher', {'event': 'command', 'name': 'previous', 'args': None})

                    case Key.ALT_L:
                        actor_system.send('MediaDispatcher', {'event': 'command', 'name': 'next', 'args': None})

                    case Key.SPACE:
                        actor_system.send('MediaDispatcher', Message(sig=Sig.PLAY_PAUSE))

                    case Key.DOT:
                        (recipient, response) = eval_cmd('..')
                        actor_system.send(recipient, response)

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
                        actor_system.send('MediaDispatcher', Message(sig=Sig.VOLUME_INC, args=arg))

                    case (Key.d | Key.D):
                        actor_system.send('Display', Message(sig=Sig.PLAYBACK_OVERLAY))

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
                        actor_system.send('MediaDispatcher', Message(sig=Sig.SEEK, args=arg))

                    case p if p in num_mapping:
                        (recipient, response) = eval_cmd(num_mapping[p])
                        actor_system.send(recipient, response)

                    case _:
                        self.logger.warning(f'Unhandled key press: {args}')

    def init(self) -> None:
        # self.sidecar = actor_system.create_actor(InputIO)
        self.sidecar = create(InputIO)

    def terminate(self) -> None:
        actor_system.send('ActorSystem', Message(sig=Sig.EXIT))
        raise SystemExit
