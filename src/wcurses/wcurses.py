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


def _draw_screen(win, height, width):
    idx = 0
    def inner(s: str|list[str], display_mode: int, term_blank: int):
        nonlocal idx

        if isinstance(s, list) or isinstance(s, deque):
            ####
            buffer = []
            for sub in s:
                if len(buffer) < (display_mode - 1):
                    buffer.append(sub)
                else:
                    buffer.append(sub)
                    win.addstr(idx, 0, f"{''.join(buffer)}{' ' * term_blank}"[:width])
                    idx += 1
                    idx = idx % height
                    buffer.clear()
            ####
            return
            if display_mode == 1:
                for sub in s:
                    win.addstr(idx, 0, sub[:width])
                    idx += 1
                    idx = idx % height

            elif display_mode == 2:
                buffer = []
                for sub in s:
                    if not buffer:
                        buffer.append(sub)
                        continue
                    else:
                        buffer.append(sub)
                        win.addstr(idx, 0, f"{''.join(buffer)}{' ' * term_blank}"[:width])
                        idx += 1
                        idx = idx % height
                        buffer.clear()

            elif display_mode == 3:
                buffer = []
                for sub in s:
                    if len(buffer) < 2:
                        buffer.append(sub)
                    else:
                        buffer.append(sub)
                        win.addstr(idx, 0, f"{''.join(buffer)}{' ' * term_blank}"[:width])
                        idx += 1
                        idx = idx % height
                        buffer.clear()

            elif display_mode == 4:
                buffer = []
                for sub in s:
                    if len(buffer) < 3:
                        buffer.append(sub)
                    else:
                        buffer.append(sub)
                        win.addstr(idx, 0, f"{''.join(buffer)}{' ' * term_blank}"[:width])
                        idx += 1
                        idx = idx % height
                        buffer.clear()

        elif isinstance(s, str):
            win.addstr(idx, 0, s[:width])
            idx += 1
            idx = clamp(0, height-2, idx)

        else:
            raise TypeError

    return inner

# def draw_logs():
#     ...

init()
