from audioop import reverse
import curses
from math import ceil

from rich.console import Console

from ..base import Actor, Message, Sig, actor_system
from . import helpers

from ...wcurses import stdscr, _draw_screen, draw_popup, draw_overlay


class Display(Actor):
    def __init__(self, pid: int, name='',parent: Actor=None, **kwargs) -> None:
        super().__init__(pid, name, parent, **kwargs)
        self.DEBUG = 0
        self.LOGS = 0

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
                height, width = stdscr.getmaxyx()
                # width = width // 2 if self.LOGS else width
                width = 0 if self.LOGS else width

                len_dir = len(dir_list) - 1
                len_files = len(files_list) - 1
                total_y_len = len_dir + len_files + 6
                display_mode = ceil( total_y_len / (height - 1) )
                display_mode = 1 if not display_mode else display_mode

                term_blank = 0
                if width % display_mode != 0:
                    term_blank = width % display_mode
                display_width = width // display_mode

                # (display_mode, term_blank, display_width) = helpers.get_term_dimensions(dir_list, files_list)
                (str_object, padding, blank) = helpers.string_format(dir_list, files_list, display_width)

                # height, width = stdscr.getmaxyx()
                main_win = curses.newwin(height, width, 0, 0)
               
                draw_screen = _draw_screen(main_win, height, width)
                main_win.clear()
                draw_screen(str_object, display_mode, term_blank)
                main_win.refresh()
                # disp(display_mode, term_blank, str_object, padding, blank)

            case Message(sig=Sig.POPUP, args=args):
                draw_popup(args)

            case Message(sig=Sig.PLAY):
                ...
                # val = msg.args.split('/')[-1]
                # draw_overlay(val)

            case Message(sig=Sig.ERROR, args=args):
                actor_system.send('Display', Message(Sig.LOGS, args))

            case Message(sig=Sig.POISON, args=args):
                raise Exception(f'{msg!r}')

            case _:
                raise SystemExit(f'{msg=}')

    def terminate(self):
        ...