from typing import Any
import os
from typing import Any
from math import ceil
from itertools import zip_longest

from rich.text import Text
from rich.console import Console

from .constants import character_encoding as ce
from ...fix_encoding import Str


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
    str_object.append(padding)
    str_object.append(format_line('DIRS', '0', pad, display_width))
    str_object.append(padding)

    for i, v in enumerate(dir_list[1:]):
        str_object.append(format_line(v, i+1, pad, display_width))

    str_object.append(padding)
    str_object.append(format_line('FILES', '0', pad, display_width))
    str_object.append(padding)

    for i, v in enumerate(files_list[1:]):
        str_object.append(format_line(v[0], i+1, pad, display_width))
    if files_list[1:]:
        str_object.append(padding)

    return str_object, padding, blank


def _disp(console: Console) -> None:
    def inner(
        display_mode: int, 
        term_blank: int, 
        str_object: list[Any], 
        padding: str, 
        blank: str
    ) -> None:
        if display_mode == 1:
            for i, v in enumerate(str_object):
                text = Text(f"{v}{' ' * term_blank}")
                text.stylize("green")
                console.print(text)

        elif display_mode == 2:
            l = len(str_object) // 2
            row1 = str_object[:l].copy()
            row1.append(padding)
            row2 = str_object[l:].copy()
            row2.insert(0, padding)
            it = zip_longest(row1, row2, fillvalue=blank)
            for i in it:
                text = Text(f"{''.join(i)}{' ' * term_blank}")
                text.stylize("green")
                console.print(text)

        elif display_mode == 3:
            l = len(str_object) // 3
            row1 = str_object[:l].copy()
            row1.append(padding)
            row2 = str_object[l:l*2].copy()
            row2.insert(0, padding)
            row2.append(padding)
            row3 = str_object[l*2:].copy()
            row3.insert(0, padding)

            it = zip_longest(row1, row2, row3, fillvalue=blank)
            for i in it:
                text = Text(f"{''.join(i)}{' ' * term_blank}")
                text.stylize("green")
                console.print(text)

        elif display_mode == 4:
            l = len(str_object) // 4
            row1 = str_object[:l].copy()
            row1.append(padding)
            row2 = str_object[l:l*2].copy()
            row2.insert(0, padding)
            row2.append(padding)
            row3 = str_object[l*2:l*3].copy()
            row3.insert(0, padding)
            row3.append(padding)
            row4 = str_object[l*3:].copy()
            row4.insert(0, padding)

            it = zip_longest(row1, row2, row3, row4, fillvalue=blank)
            for i in it:
                text = Text(f"{''.join(i)}{' ' * term_blank}")
                text.stylize("green")
                console.print(text)

        else:
            print("Too Much Files to Display. Please Reduce Character Size and Refresh ('r').")

    return inner


def get_term_dimensions(
    dir_list: list[Any], 
    files_list: list[Any]
) -> tuple[int, int, int]:
        term_x, term_y = os.get_terminal_size(0)

        len_dir = len(dir_list) - 1
        len_files = len(files_list) - 1
        total_y_len = len_dir + len_files + 6
        display_mode = ceil( total_y_len / (term_y - 1) )
        display_mode = 1 if not display_mode else display_mode

        term_blank = 0
        if term_x % display_mode != 0:
            term_blank = term_x % display_mode
        display_width = term_x // display_mode

        return display_mode, term_blank, display_width
