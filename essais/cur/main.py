import curses
import select


def main(stdscr):
    # Clear screen
    stdscr.clear()
    res = []
    for n in range(1):
        val = stdscr.getch()
        res.append(val)
    return res


def poller(stdscr) -> None:
    stdscr.nodelay(1)
    while 1:
        rr, _, _ = select.select([stdscr.getch], [], [])
        idx = 0
        if rr:
            v = rr[0]
            stdscr.addstr(idx, 0, v)
            idx += 1
            stdscr.refresh()


def test(stdscr):
    height=25 
    width=58 
    y_ofst=0 
    x_ofst=0
    row=24
    col=29
    # row=24 col=29 max_col=29 display_mode=2 height=25 width=58 err=error('addwstr() returned ERR')
    win = curses.newwin(height, width, y_ofst, x_ofst)
    win.addstr(row, col, ' ' * col)


# print(wrapper(main))
# wrapper(poller)
print(curses.wrapper(test))
