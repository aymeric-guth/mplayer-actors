import select
import sys
import os
import curses

from ..base import Actor, Message, Sig, actor_system
from ..base.actor_system import ActorGeneric
from ...wcurses import stdscr, draw_prompt, draw_popup

from .constants import num_mapping, Key



class Input(Actor):
    def __init__(self, pid: int, name='', parent: Actor=None, **kwargs) -> None:
        super().__init__(pid, name, parent, **kwargs)
        self.LOG = 0
        self._prompt_mode = 0
        self.buff: list[str] = []

    def run(self) -> None:
        while 1:
            c = stdscr.getch()
            if c == -1:
                continue
            elif self.prompt_mode:
                match c:
                    case Key.ENTER:
                        self.prompt_mode = 0
                        actor_system.send('Dispatcher', Message(sig=Sig.PARSE, args=''.join(self.buff)))
                        self.buff.clear()
                        continue
                    case Key.BACKSPACE:
                        if self.buff:
                            self.buff.pop(-1)
                    case _:
                        self.buff.append(chr(c))
                    
                actor_system.send('Display', Message(sig=Sig.PROMPT, args=self.buff.copy()))
                continue

            match c:
                case -1:
                    ...

                case 0:
                    ...

                case Key.COLON:
                    self.prompt_mode = 1

                case Key.q | Key.Q:
                    return 0

                case Key.r | Key.R:
                    actor_system.send('Dispatcher', Message(sig=Sig.PARSE, args='refresh'))

                case Key.p | Key.P:
                    actor_system.send('Dispatcher', Message(sig=Sig.PARSE, args='play'))

                case Key.ALT_H:
                    actor_system.send('MediaDispatcher', Message(sig=Sig.PREVIOUS))

                case Key.ALT_L:
                    actor_system.send('MediaDispatcher', Message(sig=Sig.NEXT))

                case Key.SPACE:
                    actor_system.send('MediaDispatcher', Message(sig=Sig.PLAY_PAUSE))

                case Key.DOT:
                    actor_system.send('Dispatcher', Message(sig=Sig.PARSE, args='..'))

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
                    actor_system.send('MediaDispatcher', Message(sig=Sig.SEEK, args=arg))

                case p if p in num_mapping:
                    actor_system.send('Dispatcher', Message(sig=Sig.PARSE, args=num_mapping[p]))
    
    @property
    def prompt_mode(self) -> int:
        return self._prompt_mode

    @prompt_mode.setter
    def prompt_mode(self, value) -> None:
        self._prompt_mode = value
        actor_system.send('Display', Message(sig=Sig.PROMPT, args=self._prompt_mode))
