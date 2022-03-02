import select
import sys
import os
import curses

from ..base import Actor, Message, Sig, actor_system
from ..base.actor_system import ActorGeneric
from ...wcurses import stdscr, draw_prompt, draw_popup


num_mapping: dict[int, int] = {
    49: '1', 
    50: '2', 
    51: '3', 
    52: '4', 
    53: '5', 
    54: '6', 
    55: '7', 
    56: '8', 
    57: '9', 
    48: '10', 
    33: '11', 
    64: '12', 
    35: '13', 
    36: '14', 
    37: '15', 
    94: '16', 
    38: '17', 
    42: '18', 
    40: '19', 
    41: '20'
}


class Input(Actor):
    def __init__(self, pid: int, name='', parent: Actor=None, **kwargs) -> None:
        super().__init__(pid, name, parent, **kwargs)
        self.DEBUG = 0

    def run(self) -> None:
        while 1:
            c = stdscr.getch()
            # actor_system.send('Logger', Message(Sig.PUSH, f'{self} got new c={c}'))

            match c:
                case 0:
                    ...
                
                case curses.KEY_RESIZE | curses.KEY_REFRESH:
                    actor_system.send('Display', Message(sig=Sig.REFRESH))
        
                case 58:
                    cmd = draw_prompt()
                    actor_system.send('Dispatcher', Message(sig=Sig.PARSE, args=cmd.decode('utf-8')))

                case 113 | 81:
                    return 0
                
                case 100:
                    actor_system.send('Display', Message(sig=Sig.LOGS))

                # r - R
                case 114 | 82:
                    actor_system.send('Dispatcher', Message(sig=Sig.PARSE, args='refresh'))
                # p - P
                case 112 | 80:
                    actor_system.send('Dispatcher', Message(sig=Sig.PARSE, args='play'))
                # alt + h
                case 153:
                    actor_system.send('MediaDispatcher', Message(sig=Sig.PREVIOUS))
                # alt + l
                case 172:
                    actor_system.send('MediaDispatcher', Message(sig=Sig.NEXT))
                # spacebar
                case 32:
                    actor_system.send('MediaDispatcher', Message(sig=Sig.PLAY_PAUSE))
                case 46:
                    actor_system.send('Dispatcher', Message(sig=Sig.PARSE, args='..'))

                case (72 | 76 | 74 | 75) as p:
                    match p:
                        # H
                        case 72:
                            arg = -5
                        # L
                        case 76:
                            arg = 5
                        # J
                        case 74:
                            arg = -10
                        # K
                        case 75:
                            arg = 10
                    actor_system.send('MediaDispatcher', Message(sig=Sig.VOLUME_INC, args=arg))

                case 99:
                    actor_system.send('Display', Message(Sig.POISON))

                case (curses.KEY_LEFT | 104 | curses.KEY_RIGHT | 108 | curses.KEY_UP | 107 | curses.KEY_DOWN | 106) as p:
                    match p:
                        case curses.KEY_LEFT | 104:
                            arg = -5
                        case curses.KEY_RIGHT | 108:
                            arg = 5
                        case curses.KEY_UP | 107:
                            arg = 60
                        case curses.KEY_DOWN | 106:
                            arg = -60
                    actor_system.send('MediaDispatcher', Message(sig=Sig.SEEK, args=arg))

                case p if p in num_mapping:
                    actor_system.send('Dispatcher', Message(sig=Sig.PARSE, args=num_mapping[p]))

            actor_system.send('Display', Message(sig=Sig.REFRESH))

