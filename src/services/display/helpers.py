from typing import Any, Callable
from math import ceil
import curses
from pathlib import Path
from collections import deque

from ...external.fix_encoding import Str
from ...external.fix_ideo import StrIdeo
from ...utils import clamp

from .constants import PROMPT


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

# def format_line(string: str, indice: int, pad: int, display_width: int) -> str:
#     string = StrIdeo(str(Str(string)))
    
#     indice = f"{indice:0{pad}}"
#     size_cell_a = len(indice) + 5
#     size_cell_b = display_width - size_cell_a
#     left_space = size_cell_b - 2 - len(string)

#     if left_space >= 0:
#         return f"| {indice} | {string}{' ' * left_space} |"
#     else:
#         return f"| {indice} | {string[:left_space-3]}... |"


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
    height: int, 
    width: int
) -> Callable[[Any, list[str], int], None]:
    row = 0
    col = 0
    def inner(self, s: list[str], display_mode: int) -> None:
        nonlocal row
        nonlocal col

        if not isinstance(s, list) and not isinstance(s, deque):
            raise TypeError

        max_col = width // display_mode

        for sub in s:
            try:
                win.addstr(row, col, sub[:max_col])
            except Exception:
                self.LOG = 1
                self.log_msg(f'{row=} {col=} {max_col=} {display_mode=} {height=} {width=}')
                self.LOG = 0
                raise

            col = col + max_col
            if col > (width - max_col):
                col = 0
                row = (row + 1) % height

    return inner


def draw_files(
    self, 
    height: int, 
    width: int, 
    y_ofst: int, 
    x_ofst: int
) -> None:
    if not height:
        return
    if not self.files_buff:
        return
    (dir_list, files_list) = self.files_buff

    len_dir = len(dir_list) - 1
    len_files = len(files_list) - 1
       
    display_mode = ceil((len_dir + len_files) / height)
    # total_y_len = len_dir + len_files + 6
    # display_mode = ceil(total_y_len / height)
    display_mode = 1 if not display_mode else display_mode
    display_width = width // display_mode

    str_object = string_format(dir_list, files_list, display_width)

    win = curses.newwin(height, width, y_ofst, x_ofst)
    _draw_screen(win, height, width)(self, str_object, display_mode)
    win.noutrefresh()


def draw_cmd(
    self, 
    height: int, 
    width: int, 
    y_ofst: int, 
    x_ofst: int
) -> None:
    if not height:
        return
    if self.cmd_buff and self.cmd_buff[-1] == '\n':
        return

    win = curses.newwin(height, width, y_ofst, x_ofst)
    win.box()
    curses.curs_set(1)
    s = f'{PROMPT}{"".join(self.cmd_buff)}'
    win.addstr(1, 1, s)
    win.move(1, len(s) + 1)
    win.noutrefresh()


def draw_playback(
    self, 
    height: int, 
    width: int, 
    y_ofst: int, 
    x_ofst: int
) -> None:
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
