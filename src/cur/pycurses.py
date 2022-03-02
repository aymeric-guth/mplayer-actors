from distutils.debug import DEBUG
from re import L
import sys
import os
import time
from pathlib import Path
import curses
from curses.textpad import Textbox, rectangle


DEBUG = 0

path = Path(__file__).parent.parent

{
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

def draw_prompt(stdscr) -> str:
    win = curses.newwin(3, curses.COLS, curses.LINES-3, 0)
    win.box()

    curses.echo()
    win.addstr(1, 1, ' >>>')
    win.move(1, 6)

    win.noutrefresh()
    # stdscr.noutrefresh()
    curses.doupdate()
    
    stdscr.move(curses.LINES-2, 6)
    message = stdscr.getstr(curses.LINES-2, 6)

    curses.noecho()

    return message


def _draw_logs(win, height):
    idx = 1
    def inner(s: str|list[str]):
        nonlocal idx

        if isinstance(s, list):
            for sub in s:
                win.addstr(idx, 1, sub)
                idx += 1
                idx = idx % height
        elif isinstance(s, str):
            win.addstr(idx, 1, s)
            idx += 1
            idx = idx % height

        else:
            raise TypeError

    return inner


def _draw_screen(win, height):
    idx = 1
    def inner(s: str|list[str]):
        nonlocal idx

        if isinstance(s, list):
            for sub in s:
                win.addstr(idx, 1, sub)
                idx += 1
                idx = idx % height
        elif isinstance(s, str):
            win.addstr(idx, 1, s)
            idx += 1
            idx = idx % height

        else:
            raise TypeError

    return inner


def draw_menu(stdscr):
    global DEBUG
    k = 0

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

    # Loop where k is the last character pressed
    while 1:
        # Declaration of strings
        title = "Curses example"
        subtitle = "Written by Clay McLeod"
        keystr = "Last key pressed: {}".format(k)

        match k:
            case 0:
                keystr = "No key press detected..."
    
            case 58:
                k = draw_prompt(main_win)
                continue

            case 113 | 81:
                return 0
            
            case 100:
                DEBUG = not DEBUG
 
        # Initialization
        max_height, max_width = stdscr.getmaxyx()
        width = max_width // 2 if DEBUG else max_width
        height = max_height

        main_win = curses.newwin(height, width, 0, 0)
        main_win.clear()
        main_win.box()
        debug_win = curses.newwin(height, width, 0, width)
        debug_win.clear()
        draw_logs = _draw_logs(debug_win, height)
        debug_win.box()
        
        idx = 0

        # Centering calculations
        start_x_title = int((width // 2) - (len(title) // 2) - len(title) % 2)
        start_x_subtitle = int((width // 2) - (len(subtitle) // 2) - len(subtitle) % 2)
        start_x_keystr = int((width // 2) - (len(keystr) // 2) - len(keystr) % 2)
        start_y = int((height // 2) - 2)

        if DEBUG:
            draw_logs([f'{start_x_title=}', f'{start_x_subtitle=}', f'{start_x_keystr=}', f'{start_y=}'])

        # Rendering some text
        whstr = "Width: {}, Height: {}".format(width, height)
        main_win.addstr(1, 1, whstr, curses.color_pair(1))

        # Render status bar
        main_win.attron(curses.color_pair(3))
        main_win.attroff(curses.color_pair(3))

        # Turning on attributes for title
        main_win.attron(curses.color_pair(2))
        main_win.attron(curses.A_BOLD)

        # Rendering title
        main_win.addstr(start_y, start_x_title, title)

        # Turning off attributes for title
        main_win.attroff(curses.color_pair(2))
        main_win.attroff(curses.A_BOLD)

        # Print rest of text
        main_win.addstr(start_y + 1, start_x_subtitle, subtitle)
        main_win.addstr(start_y + 3, (width // 2) - 2, '-' * 4)
        main_win.addstr(start_y + 5, start_x_keystr, keystr)

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
