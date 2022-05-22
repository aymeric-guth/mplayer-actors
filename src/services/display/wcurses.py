import curses
import logging
import select
import sys

from ...utils import SingletonMeta, clamp
from ...external.actors import Actor, Message, Sig, send, DispatchError, Event, Request, Response, ActorIO, create
from ...wcurses import stdscr
from .constants import PROMPT



class InputIO(ActorIO):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.log_lvl = logging.WARNING

    def run(self) -> None:
        while 1:
            rr, _, _ = select.select([sys.stdin], [], [])
            send(self.parent, Event(type='io', name='read-ready'))


class Curses(Actor):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.stdscr = stdscr
        self.child: int
        # curses.cbreak()
        # curses.noecho()
        # curses.curs_set(0)
        # self.stdscr.keypad(True)
        self.log_lvl = logging.ERROR

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except DispatchError:
            return

        match msg:
            case Request(type='render', name='cmd', args=args):
                (cmd_dims, cmd_buff) = args
                (width, height, x_ofst, y_ofst, cmd_buff) = cmd_dims
                if not height or cmd_buff and cmd_buff[-1] == '\n':
                    return
                win = curses.newwin(height, width, y_ofst, x_ofst)
                win.box()
                curses.curs_set(1)
                (cmd, cur) = cmd_buff
                s = f'{PROMPT}{"".join(cmd)}'
                win.addstr(1, 1, s[:width])
                win.move(1, cur+len(PROMPT)+1)
                win.noutrefresh()
                send(self.pid, Event(type='rendered'))

            case Event(type='rendered'):
                curses.doupdate()

            case Event(type='io', name='read-ready'):
                c = self.stdscr.getch()
                send('Input', Event(type='io', name='keypress', args=c))

            case _:
                raise DispatchError(f'Unprocessable msg={msg}')


    def init(self) -> None:
        self.child = create(InputIO)
