import sys
import os
import time
from pathlib import Path
import pickle
import curses


DEBUG = 0

path = Path(__file__).parent.parent.parent / 'cache.pckl'
with open(path, 'rb') as f:
    raw_data = pickle.load(f)
    raw_data = raw_data[:100]

num_mapping: dict[int, int] = {
    49: 1, 
    50: 2, 
    51: 3, 
    52: 4, 
    53: 5, 
    54: 6, 
    55: 7, 
    56: 8, 
    57: 9, 
    48: 10, 
    33: 11, 
    64: 12, 
    35: 13, 
    36: 14, 
    37: 15, 
    94: 16, 
    38: 17, 
    42: 18, 
    40: 19, 
    41: 20
}


def draw_prompt(height, width) -> bytes:   
    prompt_win = curses.newwin(3, width, height-3, 0)
    prompt_win.box()

    curses.echo()
    curses.curs_set(1)
    prompt_win.addstr(1, 1, ' >>>')
    prompt_win.move(1, 6)

    prompt_win.noutrefresh()
    curses.doupdate()
    
    prompt_win.move(1, 6)
    message = prompt_win.getstr(1, 6)

    curses.noecho()
    curses.curs_set(0)

    return message


def clamp(lo, hi, val):
    return min(max(lo, val), hi)


def _draw_screen(win, height, width):
    idx = 1
    def inner(s: str|list[str]):
        nonlocal idx

        if isinstance(s, list):
            for sub in s:
                win.addstr(idx, 1, sub[:width-2])
                idx += 1
                idx = idx % height

        elif isinstance(s, str):
            win.addstr(idx, 1, s[:width-2])
            idx += 1
            idx = clamp(1, height-2, idx)

        else:
            raise TypeError

    return inner


def draw_popup(stdscr, s: str) -> None:
    max_height, max_width = stdscr.getmaxyx()
    height, width = 3, max_width // 4
    offset_x = (max_width - width) // 2
    offset_y = (max_height - height) // 2
    popup = curses.newwin(height, width, offset_y, offset_x)
    
    ofst = clamp(1, width, (width - len(s)) // 2)
    popup.addstr(1, ofst, s[:width-3])
    popup.box()
    popup.refresh()


def draw_menu(stdscr):
    global DEBUG
    k = 0

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()

    while 1:
        match k:
            case 0:
                ...
    
            case 58:
                k = draw_prompt(height, width)
                continue

            case 113 | 81:
                return 0
            
            case 100:
                DEBUG = not DEBUG

            case curses.KEY_LEFT | curses.KEY_RIGHT | curses.KEY_UP | curses.KEY_DOWN | 104 | 106 | 107 | 108 | 32 as p:
                match p:
                    # spacebar
                    case 32:
                        ...
                    case curses.KEY_LEFT | 104:
                        ...
                    case curses.KEY_RIGHT | 108:
                        ...
                    case curses.KEY_UP | 107:
                        ...
                    case curses.KEY_DOWN | 106:
                        ...

                draw_popup(stdscr, f'Got mpv-key {k}')
                time.sleep(0.5)

            case p if p in num_mapping:
                draw_popup(stdscr, f'Selected {num_mapping[p]}')
                time.sleep(0.5)
 
            case p if isinstance(p, bytes):
                draw_popup(stdscr, f'Got {p.decode("utf-8")}')
                time.sleep(0.5)

        # Initialization
        max_height, max_width = stdscr.getmaxyx()
        width = max_width // 2 if DEBUG else max_width
        height = max_height

        main_win = curses.newwin(height, width, 0, 0)
        main_win.clear()
        main_win.box()
        debug_win = curses.newwin(height, width, 0, width)
        debug_win.clear()
        draw_logs = _draw_screen(debug_win, height, width)
        debug_win.box()

        draw_logs([
            f'{max_height=}', 
            f'{max_width=}', 
            f'{width=}', 
            f'{height=}'
        ])
        

        draw_screen = _draw_screen(main_win, height, width)
        for i in raw_data:
            r = (
                i.get('path'),
                i.get('filename'),
                i.get('extension')
            )
            
            try:
                draw_screen(''.join(r))    
            except Exception:
                curses.endwin()
                raise

        # Refresh the screen
        debug_win.refresh()
        main_win.refresh()

        # Wait for next input
        k = stdscr.getch()


def main():    
    stdscr = curses.initscr()
    curses.cbreak()
    curses.noecho()
    curses.curs_set(0)
    stdscr.keypad(True)

    try:
        return draw_menu(stdscr)
    finally:
        curses.nocbreak()
        curses.echo()
        curses.curs_set(1)
        stdscr.keypad(False)
        stdscr = None

if __name__ == "__main__":
    sys.exit(main())
