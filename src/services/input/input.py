import curses
from collections import deque

from ..base import Actor, Message, Sig, actor_system, ActorGeneric
from ...wcurses import stdscr


from .constants import num_mapping, Key
from .helpers import CmdCache, eval_cmd



class Input(Actor):
    def __init__(self, pid: int, parent: ActorGeneric, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self._prompt_mode = 0
        self.buff: list[str] = []

    def run(self) -> None:
        while 1:
            c = stdscr.getch()
            self.logger.info(f'Got new input c={c}')
            if c == -1: continue
            self.dispatch(self, Message(sig=Sig.PARSE, args=c))

    def dispatch(self, sender: ActorGeneric, msg: Message) -> None:
        c = msg.args
        if self.prompt_mode:
            match c:
                case Key.ENTER:
                    self.prompt_mode = 0
                    (recipient, response) = eval_cmd(''.join(self.buff))
                    CmdCache().push(self.buff)
                    self.buff.clear()
                    actor_system.send(recipient, response)
                    return

                case Key.BACKSPACE:
                    self.buff.pop() if self.buff else None

                case curses.KEY_UP:
                    self.buff = CmdCache().prev()

                case curses.KEY_DOWN:
                    self.buff = CmdCache().next()

                case _:
                    self.buff.append(chr(c))
                
            actor_system.send('Display', Message(sig=Sig.PROMPT, args=self.buff.copy()))
            return

        match c:
            case 0:
                ...

            case Key.COLON:
                self.prompt_mode = 1

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
                actor_system.send('MediaDispatcher', Message(sig=Sig.PREVIOUS))

            case Key.ALT_L:
                actor_system.send('MediaDispatcher', Message(sig=Sig.NEXT))

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

            case Key.c:
                actor_system.send('Display', Message(Sig.POISON))

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
                self.logger.warning(f'Unhandled key press: {c}')

    @property
    def prompt_mode(self) -> int:
        return self._prompt_mode

    @prompt_mode.setter
    def prompt_mode(self, value) -> None:
        self._prompt_mode = value
        actor_system.send('Display', Message(sig=Sig.PROMPT, args=self._prompt_mode))

    def terminate(self) -> None:
        raise SystemExit('SIGQUIT')
