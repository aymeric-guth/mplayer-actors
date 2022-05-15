import curses
import logging
from typing import Optional

from ...external.actors import Actor, Message, Sig, actor_system
from ...wcurses import stdscr


from .constants import num_mapping, Key
from .helpers import CmdCache, eval_cmd, CmdBuffer
from ...utils import SingletonMeta


class Prompt(Actor):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.log_lvl = logging.ERROR
        self.post(Message(sig=Sig.INIT))

    def dispatch(self, sender: int, msg: Message) -> None:
        self.logger.info(f'New message: {msg}')
        match msg:
            case Message(sig=Sig.INIT):
                actor_system.send('Display', Message(sig=Sig.PROMPT, args=True))

            case Message(sig=Sig.TERMINATE):
                actor_system.send('ActorSystem', Message(sig=Sig.TERMINATE))

            case Message(sig=Sig.PARSE, args=args):
                match args:
                    case Key.ENTER:
                        CmdCache().push(CmdBuffer().get())
                        actor_system.send('Display', Message(sig=Sig.PROMPT, args=False))
                        # actor_system.send(self.parent, Message(sig=Sig.PARSE, args=CmdBuffer().to_str()))
                        actor_system.send(self.parent, {'event': 'command', 'name': 'parse', 'args': CmdBuffer().to_str()})
                        CmdBuffer().clear()
                        self.post(Message(sig=Sig.TERMINATE))

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

    def terminate(self) -> None:
        self.logger.warning(f'{self} terminated')
        raise SystemExit


class InputIO(Actor, metaclass=SingletonMeta):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.log_lvl = logging.WARNING

    def run(self) -> None:
        while 1:
            c = stdscr.getch()
            self.logger.info(f'Got new input c={c}')
            if c == -1: 
                continue
            actor_system.send(self.parent, {'event': 'io', 'name': 'key', 'args': c})
            # actor_system.send(self.parent, Message(sig=Sig.PARSE, args=c))


class Input(Actor, metaclass=SingletonMeta):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.log_lvl = logging.INFO
        self.child: Optional[int] = None
        self.sidecar: int
        self.post(Message(sig=Sig.INIT))

    def dispatch(self, sender: int, msg: Message) -> None:
        self.logger.error(f'child={self.child}')
        match msg:
            case Message(sig=Sig.INIT):
                self.sidecar = actor_system.create_actor(InputIO)

            case {'event': 'command', 'name': 'parse', 'args': args}:
                self.child = None
                (recipient, response) = eval_cmd(args)
                actor_system.send(recipient, response)

            case {'event': 'io', 'name': 'key', 'args': args} if self.child is not None:
                actor_system.send(self.child, Message(sig=Sig.PARSE, args=args))

            case {'event': 'io', 'name': 'key', 'args': args}:
                match args:
                    case 0:
                        ...

                    case Key.COLON:
                        self.child = actor_system.create_actor(Prompt)

                    case Key.q | Key.Q:
                        actor_system.post(Message(sig=Sig.SIGQUIT))
                        self.terminate()

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

    # @property
    # def prompt_mode(self) -> bool:
    #     return self._prompt_mode

    # @prompt_mode.setter
    # def prompt_mode(self, value: bool) -> None:
    #     self._prompt_mode = value
    #     actor_system.send('Display', Message(sig=Sig.PROMPT, args=self._prompt_mode))

    def terminate(self) -> None:
        raise SystemExit('SIGQUIT')
