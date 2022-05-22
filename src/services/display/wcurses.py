import curses
import logging
import select
import sys
from typing import Optional
from pathlib import Path
from math import ceil

from ...utils import SingletonMeta, clamp
from ...external.actors import Actor, Message, Sig, send, DispatchError, Event, Request, Response, ActorIO, create
from ...wcurses import stdscr
from .helpers import string_format
from .constants import PROMPT



class InputIO(ActorIO):
    def __init__(self, pid: int, parent: int, name='', stdscr: Optional[curses.window]=None, **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        if stdscr is None:
            raise SystemExit
        self.stdscr = stdscr
        self.log_lvl = logging.WARNING

    def run(self) -> None:
        while 1:
            c = self.stdscr.getch()
            # rr, _, _ = select.select([sys.stdin], [], [])
            # c = rr[0].read()
            # self.logger.error(repr(Event(type='io', name='read-ready', args=c)))
            send(self.parent, Event(type='io', name='read-ready', args=c))


class Curses(Actor):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.stdscr = stdscr
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
            case Request(type='render', name='cmd', args=(cmd_dims, cmd_buff)):
                (width, height, x_ofst, y_ofst) = cmd_dims
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

            case Event(type='io', name='read-ready', args=args) as msg:
                # c = self.stdscr.getch()
                # send('Input', Event(type='io', name='keypress', args=c))
                send('Input', Event(type='io', name='keypress', args=args))

            case Request(type='render', name='playback', args=(playback_dims , media_meta)):
                (width, height, x_ofst, y_ofst) = playback_dims
                if not height:
                    return

                player_state = media_meta.get('player-state', 0)
                file = media_meta.get('file', '')
                file = Path(file).name if file else file
                current, total = media_meta.get('pos', (0, 0))
                volume = media_meta.get('volume', 0)
                # percent_pos = self.media_meta.get('percent-pos', 0.)
                playback_time = media_meta.get('playback-time', 0)
                playback_time = 0 if playback_time is None else int(playback_time)
                playtime_remaining = media_meta.get('playtime-remaining', 0)
                playtime_remaining = 0 if playtime_remaining is None else int(playtime_remaining)
                duration = media_meta.get('duration', 0.)
                duration = 0 if duration is None else int(duration)
                metadata = media_meta.get('metadata', '')

                win = curses.newwin(height, width, y_ofst, x_ofst)
                win.addstr(1, 2, f'File: {file}')

                pos = f'Position: {current}/{total} | '
                win.addstr(2, 2, pos)

                pb_mode = media_meta.get('playback-mode', 'Normal')
                pb_mode = f'Playback: {pb_mode}'
                win.addstr(2, 2+len(pos), pb_mode)

                media_state = f'Media State: {player_state}'
                win.addstr(3, 2, media_state)
                volume = f' | Volume: {volume}%'
                win.addstr(3, 2 + len(media_state), volume)
                playback = f' | Playback: {playback_time:03} / {duration:03} s'
                # playback = f' | {percent_pos:.1f}%'
                win.addstr(3, 2 + len(media_state) + len(volume), playback)

                # playback_time
                # playtime_remaining
                # duration
                win.box()
                win.noutrefresh()
                send(self.pid, Event(type='rendered'))

            case Request(type='render', name='files', args=(files_dims , files_buff)):
                (width, height, x_ofst, y_ofst) = files_dims
                if not height or not files_buff:
                    return
                height -= 1

                (dir_list, files_list) = files_buff
                blocks = len(dir_list) + len(files_list)
                display_mode = ceil(blocks / height)
                display_mode = 1 if not display_mode else display_mode
                display_width = width // display_mode

                win = curses.newwin(height+1, width, y_ofst, x_ofst)
                row, col = 0, 0
                max_col = width // display_mode

                for sub in string_format(dir_list, files_list, display_width):
                    try:
                        win.addstr(row, col, sub[:max_col])
                    except Exception as err:
                        self.logger.error(f'{row=} {col=} {max_col=} {display_mode=} {height=} {width=} {sub=} {err=}')
                        raise

                    col = col + max_col
                    if col > (width - max_col):
                        col = 0
                        row = (row + 1) % height
                win.noutrefresh()
                send(self.pid, Event(type='rendered'))


            case _:
                raise DispatchError(f'Unprocessable msg={msg}')


    def init(self) -> None:
        create(InputIO, stdscr=self.stdscr)
