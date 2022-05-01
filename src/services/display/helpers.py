from typing import Any
import os
from typing import Any
from math import ceil
from itertools import zip_longest
import curses

from rich.text import Text
from rich.console import Console

from .constants import character_encoding as ce
from ...fix_encoding import Str
from ...wcurses import stdscr, _draw_screen, draw_popup, draw_overlay

from .constants import PROMPT



def display_len(string: str) -> int:
        offset = 0
        for s in string:
            if s in ce.modifier: 
                offset -= 1
            elif s in ce.full_width: 
                offset += 1
        return len(string) + offset


class StrIdeo:
    def __init__(self, s: str) -> None:
        if isinstance(s, Str):
            self.s = str(s)
        elif isinstance(s, str):
            self.s = s
        else:
            raise NotImplementedError

        self.is_ideo = set(s) & ce.global_ideographic
        if self.is_ideo:
            v = self.s[0]
            last = display_len(v)
            self.str_map = [ [v,], [last,] ]
            for v in self.s[1:]:
                self.str_map[0].append(v)
                current = display_len(v)
                self.str_map[1].append(last+current)
                last += current

    def __bool__(self) -> bool:
        return self.is_ideo

    def __len__(self) -> int:
        return display_len(self.s)

    def __str__(self) -> str:
        return self.s

    def __getitem__(self, value: int|slice) -> str:
        if not self.__bool__():
            return self.s[value]
        assert isinstance(value, slice), (f'{value=} {self.s=}')
        sentinel = value.stop if value.stop >= 0 else value.stop + len(self)
        for i, v in enumerate(self.str_map[1]):
            if v > sentinel:
                return ''.join(self.str_map[0][:i])
        else:
            return self.s


def format_line(string: str, indice: int, pad: int, display_width: int) -> str:
    string = StrIdeo(Str(string))
    
    indice = f"{indice:0{pad}}"
    size_cell_a = len(indice) + 5
    size_cell_b = display_width - size_cell_a
    left_space = size_cell_b - 2 - len(string)

    if left_space >= 0:
        return f"| {indice} | {string}{' ' * left_space} |"
    else:
        return f"| {indice} | {string[:left_space-3]}... |"


def string_format(dir_list: list[Any], files_list: list[Any], display_width: int) -> list[Any]:
    len_dir = len(dir_list)
    len_files = len(files_list)

    pad = 3 if (len_dir+len_files) // 10 > 10 else 2
    padding = f"*{(display_width-2) * '-'}*"
    blank = display_width * ' '

    str_object = []
    # str_object.append(padding)
    str_object.append(format_line('DIRS', '0', pad, display_width))
    # str_object.append(padding)

    for i, v in enumerate(dir_list[1:]):
        str_object.append(format_line(v, i+1, pad, display_width))

    # str_object.append(padding)
    str_object.append(format_line('FILES', '0', pad, display_width))
    # str_object.append(padding)

    for i, v in enumerate(files_list[1:]):
        str_object.append(format_line(v[0], i+1, pad, display_width))
    # if files_list[1:]:
    #     str_object.append(padding)

    return str_object, padding, blank


def draw_files(self, height: int, width: int, y_ofst: int, x_ofst: int) -> None:
    if not height:
        return
    if not self.files_buff:
        return
    (dir_list, files_list) = self.files_buff

    len_dir = len(dir_list) - 1
    len_files = len(files_list) - 1
    total_y_len = len_dir + len_files + 6
    display_mode = ceil(total_y_len / (height - 1))
    display_mode = 1 if not display_mode else display_mode

    term_blank = 0
    if width % display_mode != 0:
        term_blank = width % display_mode
    display_width = width // display_mode

    (str_object, padding, blank) = string_format(dir_list, files_list, display_width)

    win = curses.newwin(height, width, y_ofst, x_ofst)
    # win.clear()
    draw_screen = _draw_screen(win, height, width)
    draw_screen(str_object, display_mode, term_blank)
    win.noutrefresh()


def draw_cmd(self, height: int, width: int, y_ofst: int, x_ofst: int) -> None:
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


def draw_playback(self, height: int, width: int, y_ofst: int, x_ofst: int) -> None:
    if not height:
        return

    win = curses.newwin(height, width, y_ofst, x_ofst)
    win.addstr(1, 1, f'File: {self.media_meta.file}')
    current, total = self.media_meta.pos
    win.addstr(2, 1, f'Position: {current}/{total}')
    media_state = f'Media State: {self.media_meta.state}'
    win.addstr(3, 1, media_state)
    win.addstr(3, 2 + len(media_state), f'| Volume: {self.media_meta.volume}')
    win.box()
    win.noutrefresh()
