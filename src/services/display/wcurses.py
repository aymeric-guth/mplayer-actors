from typing import Any
import curses
import logging
import select
import sys
from typing import Optional
from pathlib import Path
from math import ceil
import threading
import time

from ...utils import SingletonMeta, clamp, try_not
from ...external.actors import Actor, Message, Sig, send, DispatchError, Event, Request, Response, ActorIO, create
from .helpers import string_format, set_dims
from .constants import PROMPT



class InputIO(ActorIO):
    def __init__(self, pid: int, parent: int, name='', stdscr: Optional[curses.window]=None, **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        if stdscr is None:
            raise SystemExit
        self.stdscr = stdscr
        self.log_lvl = logging.ERROR
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()

    def _run(self) -> None:
        while 1:
            c = self.stdscr.getch()
            send(to=self.parent, what=Event(type='io', name='read-ready', args=c))

    def dispatch(self, sender: int, msg: Any) -> None:
        try:
            super().dispatch(sender, msg)
        except DispatchError:
            return
            
    def terminate(self) -> None:
        try_not(self._t.join, Exception) if self._t else None
        raise SystemExit


class Curses(Actor):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.stdscr = curses.initscr()
        curses.cbreak()
        curses.noecho()
        curses.curs_set(0)
        self.stdscr.keypad(True)

        self.files_overlay = 1
        self.playback_overlay = 1
        self.cmd_overlay = 0
        self.log_lvl = logging.ERROR

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except DispatchError:
            return

        match msg:
            case Event(type='property-change', name=name, args=args):
                match name:
                    case 'files-overlay':
                        self.files_overlay = args
                    case 'cmd-overlay':
                        self.cmd_overlay = args
                        if not self.cmd_overlay:
                            curses.curs_set(0)
                    case 'playback-overlay':
                        self.playback_overlay = args
                    case 'files-buff':
                        send(self.pid, Request(type='render', name='files', args=args))
                    case 'cmd-buff':
                        send(self.pid, Request(type='render', name='cmd', args=args))

            case Request(type='render', name='cmd', args=cmd_buff):
                set_dims(self)
                (width, height, x_ofst, y_ofst) = self.cmd_dims
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
                send('Input', Event(type='io', name='keypress', args=args))

            case Request(type='render', name='playback', args=media_meta):
                set_dims(self)
                (width, height, x_ofst, y_ofst) = self.playback_dims
                if not height:
                    return

                player_state = media_meta.get('player-state', 0)
                file = media_meta.get('current-item', '')
                file = Path(file).name if file else file
                current, total = media_meta.get('playlist-pos', (0, 0))
                volume = media_meta.get('volume', 0)
                # percent_pos = self.media_meta.get('percent-pos', 0.)
                playback_time = media_meta.get('time-pos', 0)
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

            case Request(type='render', name='files', args=files_buff):
                set_dims(self)
                (width, height, x_ofst, y_ofst) = self.files_dims
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

            case Event(type='signal', name='resize'):
                curses.endwin()  # This could lead to crashes according to below comment
                self.stdscr.refresh()
                send(to=self.parent, what=Event(type='io', name='resize'))

            case _:
                raise DispatchError(f'Unprocessable msg={msg}')

    def init(self) -> None:
        create(InputIO, stdscr=self.stdscr)
        send(to=self.parent, what=Message(sig=Sig.SUBSCRIBE, args='files-overlay'))
        send(to=self.parent, what=Message(sig=Sig.SUBSCRIBE, args='cmd-overlay'))
        send(to=self.parent, what=Message(sig=Sig.SUBSCRIBE, args='playback-overlay'))
        send(to=self.parent, what=Message(sig=Sig.SUBSCRIBE, args='files-buff'))
        send(to=self.parent, what=Message(sig=Sig.SUBSCRIBE, args='cmd-buff'))

    def terminate(self) -> None:
        send(to=self.child, what=Message(sig=Sig.EXIT))
        # while self.child:
        #     time.sleep(0.1)
        self.stdscr.keypad(False)
        curses.nocbreak()
        curses.echo()
        curses.curs_set(1)       
        self.stdscr.clear()
        curses.endwin()
        raise SystemExit
