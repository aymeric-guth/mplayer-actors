from cmd import PROMPT
import curses
from typing import Any
from math import ceil
import time

from rich.console import Console

from ..base import Actor, Message, Sig, actor_system
from . import helpers

from ...wcurses import stdscr, _draw_screen, draw_popup, draw_overlay

PLAYBACK_HEIGHT = 5
CMD_HEIGHT = 3


class Display(Actor):
    def __init__(self, pid: int, name='',parent: Actor=None, **kwargs) -> None:
        super().__init__(pid, name, parent, **kwargs)
        self.DEBUG = 0
        self.LOGS = 0
        self.files_overlay = 1
        self.playback_overlay = 0
        self.cmd_overlay = 0
        self.cmd_buff: list[str] = []
        self.files_buff: list[Any] = []
        self.files_win = None
        self.cmd_win = None

    def dispatch(self, sender: Actor, msg: Message) -> None:
        match msg:
            case Message(sig=Sig.LOGS, args=None):
                self.LOGS = not self.LOGS
                if self.LOGS:
                    actor_system.send('Logger', Message(Sig.GET))

            case Message(sig=Sig.LOGS, args=args):
                height, width = stdscr.getmaxyx()
                # width = width // 2 if self.LOGS else width
                logs_win = curses.newwin(height, width, 0, 0)
                args.sort(reverse=True)
                logs_win.clear()
                _draw_screen(logs_win, height-1, width)(args, 1, 0)
                logs_win.refresh()

            case Message(sig=Sig.REFRESH, args=args):
                if self.LOGS:
                    actor_system.send('Logger', Message(Sig.GET))
                else:
                    actor_system.send('Files', Message(Sig.CWD_GET))

            case Message(sig=Sig.CWD_GET, args=args):
                dir_list, files_list = args.get('dir_list'), args.get('files_list')
                self.files_buff = [dir_list, files_list]
                self.post(None, Message(sig=Sig.DRAW_SCREEN))

            case Message(sig=Sig.PROMPT, args=args) if args is None:
                # initialisation de la fenetre du prompt
                self.cmd_overlay = 1
                self.post(None, Message(sig=Sig.DRAW_SCREEN))

            case Message(sig=Sig.PROMPT, args=args) if args and args[-1] == '\n':
                # ajout ou supression d'un caractère de la fenetre du prompt                
                self.cmd_buff.clear()
                self.cmd_overlay = 0
                curses.curs_set(0)
                self.post(None, Message(sig=Sig.DRAW_SCREEN))

            case Message(sig=Sig.PROMPT, args=args):
                self.cmd_buff = args.copy()
                self.post(None, Message(sig=Sig.DRAW_SCREEN))


            case Message(sig=Sig.DRAW_SCREEN):
                max_height, max_width = stdscr.getmaxyx()
                # stdscr.clear()
                if self.cmd_overlay:
                    cmd_width = max_width
                    cmd_height = CMD_HEIGHT
                else:
                    cmd_width = 0
                    cmd_height = 0

                if self.playback_overlay:
                    playback_width = max_width
                    playback_height = PLAYBACK_HEIGHT
                else:
                    playback_width = 0
                    playback_height = 0

                if self.files_overlay:
                    files_width = max_width
                    files_height = max_height - cmd_height - playback_height
                else:
                    files_width = 0
                    files_height = 0

                files_x_ofst = 0
                files_y_ofst = 0
                playback_x_ofst = 0
                playback_y_ofst = files_height
                cmd_x_ofst = 0
                cmd_y_ofst = files_height + playback_height

                helpers.draw_files(self, files_height, files_width, files_y_ofst, files_x_ofst)
                helpers.draw_cmd(self, cmd_height, cmd_width, cmd_y_ofst, cmd_x_ofst)
                curses.doupdate()
                

            case Message(sig=Sig.DRAW_PLAYBACK, args=args):
                (height, width, y_ofst, x_ofst) = args
                if not height:
                    return

                # width = args.get('width')
                # height = args.get('height')
                # playback_win = curses.newwin(PLAYBACK_HEIGHT, width, height, 0)
                # playback_win.clear()
                # playback_win.box()
                # playback_win.refresh()

            case Message(sig=Sig.POPUP, args=args):
                draw_popup(args)

            case Message(sig=Sig.PLAY):
                ...
                # val = msg.args.split('/')[-1]
                # draw_overlay(val)

            case Message(sig=Sig.ERROR, args=args):
                ...
                # actor_system.send('Display', Message(Sig.LOGS, args))

            case Message(sig=Sig.POISON, args=args):
                raise Exception(f'{msg!r}')

            case _:
                raise SystemExit(f'{msg=}')

    def terminate(self):
        ...