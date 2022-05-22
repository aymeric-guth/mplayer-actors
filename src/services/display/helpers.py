from typing import Any, Callable
from math import ceil
import curses
from pathlib import Path
from collections import deque

from ...external.fix_encoding import Str
from ...utils import clamp
from ...external.fix_ideo import StrIdeo

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


def set_dims(self) -> None:
    max_height, max_width = self.stdscr.getmaxyx()
    # (cmd_width, cmd_height) = (max_width, CMD_HEIGHT) if self.cmd_overlay else (0, 0)
    if self.cmd_overlay:
        cmd_width = max_width - 2
        cmd_height = CMD_HEIGHT
    else:
        cmd_width = 0
        cmd_height = 0
    # (playback_width, playback_height) = (max_width, PLAYBACK_HEIGHT) if self.playback_overlay else (0, 0)
    if self.playback_overlay:
        playback_width = max_width - 2
        playback_height = PLAYBACK_HEIGHT
    else:
        playback_width = 0
        playback_height = 0
    # (files_width, files_height) = (max_width, (max_height - cmd_height - playback_height)) if self.files_overlay else (0, 0)    
    if self.files_overlay:
        files_width = max_width
        files_height = max_height - cmd_height - playback_height
    else:
        files_width = 0
        files_height = 0

    files_x_ofst = 0
    files_y_ofst = 0
    self.files_dims = (files_width, files_height, files_x_ofst, files_y_ofst)

    playback_x_ofst = 1
    playback_y_ofst = files_height
    self.playback_dims = (playback_width, playback_height, playback_x_ofst, playback_y_ofst)
       
    cmd_x_ofst = 1
    cmd_y_ofst = files_height + playback_height
    self.cmd_dims = (cmd_width, cmd_height, cmd_x_ofst, cmd_y_ofst)


# def draw_popup(s: str) -> None:
#     global stdscr

#     max_height, max_width = stdscr.getmaxyx()
#     height, width = 3, max_width // 4
#     offset_x = (max_width - width) // 2
#     offset_y = (max_height - height) // 2
#     popup = curses.newwin(height, width, offset_y, offset_x)
    
#     ofst = clamp(1, width, (width - len(s)) // 2)
#     popup.addstr(1, ofst, s[:width-3])
#     popup.box()
#     popup.refresh()
