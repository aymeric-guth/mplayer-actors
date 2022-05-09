import curses
from collections import deque


stdscr = None

def clamp(lo, hi, val):
    return min(max(lo, val), hi)


def init():
    global stdscr

    stdscr = curses.initscr()
    curses.cbreak()
    curses.noecho()
    curses.curs_set(0)
    stdscr.keypad(True)

    # stdscr.clear()
    # stdscr.refresh()


def deinit():
    global stdscr

    curses.endwin()
    curses.nocbreak()
    curses.echo()
    curses.curs_set(1)
    stdscr.keypad(False)
    stdscr = None


def draw_prompt() -> bytes:   
    global stdscr

    height, width = stdscr.getmaxyx()
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
    curses.doupdate()

    return message


def draw_popup(s: str) -> None:
    global stdscr

    max_height, max_width = stdscr.getmaxyx()
    height, width = 3, max_width // 4
    offset_x = (max_width - width) // 2
    offset_y = (max_height - height) // 2
    popup = curses.newwin(height, width, offset_y, offset_x)
    
    ofst = clamp(1, width, (width - len(s)) // 2)
    popup.addstr(1, ofst, s[:width-3])
    popup.box()
    popup.refresh()


def draw_overlay(s: str) -> None:
    global stdscr

    max_height, max_width = stdscr.getmaxyx()
    height, width = 5, max_width // 2
    offset_x = (max_width - width) // 2
    offset_y = (max_height - height) // 2
    popup = curses.newwin(height, width, offset_y, offset_x)
    
    ofst = clamp(1, width, (width - len(s)) // 2)
    popup.addstr(2, ofst, s[:width-3])
    popup.box()
    popup.refresh()


init()
