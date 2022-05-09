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
    return curses.newwin(10, 20, 0, 0).getmaxyx()


# print(wrapper(main))
# wrapper(poller)
print(curses.wrapper(test))
