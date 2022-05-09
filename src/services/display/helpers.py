from typing import Any, Callable
from math import ceil
import curses
from pathlib import Path
from collections import deque

from ...external.fix_encoding import Str
from ...external.fix_ideo import StrIdeo
from ...wcurses import stdscr

from .constants import PROMPT, CMD_HEIGHT, PLAYBACK_HEIGHT


def format_line(
    string: str, 
    indice: int, 
    pad: int, 
    display_width: int
) -> str:
    s: StrIdeo = StrIdeo(str(Str(string)))
    idx = f"{indice:0{pad}}"
    size_cell_a = len(idx) + 5
    size_cell_b = display_width - size_cell_a
    left_space = size_cell_b - 2 - len(s)

    if left_space >= 0:
        return f"| {idx} | {s}{' ' * left_space} |"
    else:
        return f"| {idx} | {s[:left_space-3]}... |"


def string_format(
    dir_list: list[Any], 
    files_list: list[Any], 
    display_width: int
) -> list[str]:
    len_dir = len(dir_list)
    len_files = len(files_list)

    pad = 3 if (len_dir + len_files) // 10 > 10 else 2

    str_object: list[str] = []
    str_object.append(format_line('DIRS', 0, pad, display_width))
    for i, v in enumerate(dir_list[1:]):
        str_object.append(format_line(v, i+1, pad, display_width))

    str_object.append(format_line('FILES', 0, pad, display_width))
    for i, v in enumerate(files_list[1:]):
        str_object.append(format_line(v[0], i+1, pad, display_width))

    return str_object


def _draw_screen(
    win: curses.window,
    display_mode: int
) -> Callable[[Any, list[str]], curses.window]:
    (height, width) = win.getmaxyx()
    row = 0
    col = 0
    max_col = width // display_mode

    def inner(self: Any, s: list[str]) -> curses.window:
        nonlocal row, col

        if not isinstance(s, list) and not isinstance(s, deque):
            raise TypeError

        for sub in s:
            try:
                win.addstr(row, col, sub[:max_col])
            except Exception:
                with self:
                    self.log_msg(f'{row=} {col=} {max_col=} {display_mode=} {height=} {width=}')
                raise

            col = col + max_col
            if col > (width - max_col):
                col = 0
                row = (row + 1) % height
        
        return win

    return inner


def draw_files(self) -> None:
    (width, height, x_ofst, y_ofst) = self.files_dims
    if not height or not self.files_buff:
        return

    (dir_list, files_list) = self.files_buff
    blocks = len(dir_list) + len(files_list)
    display_mode = ceil(blocks / height)
    display_mode = 1 if not display_mode else display_mode
    display_width = width // display_mode

    _draw_screen(
        curses.newwin(height, width, y_ofst, x_ofst), 
        display_mode
    )(
        self, 
        string_format(dir_list, files_list, display_width)
    ).noutrefresh()


def draw_cmd(self) -> None:
    (width, height, x_ofst, y_ofst) = self.cmd_dims
    if not height or self.cmd_buff and self.cmd_buff[-1] == '\n':
        return

    win = curses.newwin(height, width, y_ofst, x_ofst)
    win.box()
    curses.curs_set(1)
    s = f'{PROMPT}{"".join(self.cmd_buff)}'
    win.addstr(1, 1, s[:width])
    win.move(1, len(s) + 1)
    win.noutrefresh()


def draw_playback(self) -> None:
    (width, height, x_ofst, y_ofst) = self.playback_dims
    if not height:
        return

    player_state = self.media_meta.get('player-state', 0)
    file = self.media_meta.get('file', '')
    file = Path(file).name if file else file
    current, total = self.media_meta.get('pos', (0, 0))
    volume = self.media_meta.get('volume', 0)
    # percent_pos = self.media_meta.get('percent-pos', 0.)
    playback_time = self.media_meta.get('playback-time', 0)
    playback_time = 0 if playback_time is None else int(playback_time)
    playtime_remaining = self.media_meta.get('playtime-remaining', 0)
    playtime_remaining = 0 if playtime_remaining is None else int(playtime_remaining)
    duration = self.media_meta.get('duration', 0.)
    duration = 0 if duration is None else int(duration)
    metadata = self.media_meta.get('metadata', '')

    win = curses.newwin(height, width, y_ofst, x_ofst)
    win.addstr(1, 1, f'File: {file}')
    win.addstr(2, 1, f'Position: {current}/{total}')
    media_state = f'Media State: {player_state}'
    win.addstr(3, 1, media_state)
    volume = f' | Volume: {volume}%'
    win.addstr(3, 1 + len(media_state), volume)
    playback = f' | Playback: {playback_time:03} / {duration:03} s'
    # playback = f' | {percent_pos:.1f}%'
    win.addstr(3, 1 + len(media_state) + len(volume), playback)

    # playback_time
    # playtime_remaining
    # duration
    win.box()
    win.noutrefresh()


def set_dims(self) -> None:
    max_height, max_width = stdscr.getmaxyx()
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
    self.files_dims = (files_width, files_height, files_x_ofst, files_y_ofst)

    playback_x_ofst = 0
    playback_y_ofst = files_height
    self.playback_dims = (playback_width, playback_height, playback_x_ofst, playback_y_ofst)
       
    cmd_x_ofst = 0
    cmd_y_ofst = files_height + playback_height
    self.cmd_dims = (cmd_width, cmd_height, cmd_x_ofst, cmd_y_ofst)