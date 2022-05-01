from curses import wrapper
import curses

from curses import wrapper

def main(stdscr):
    # Clear screen
    stdscr.clear()
    res = []
    for n in range(1):
        val = stdscr.getch()
        res.append(val)
    return res
#    files_win = curses.newwin(100, 10, 0, 0)
#    content = dir(files_win)
#    for i, v in enumerate(content):
#        files_win.addstr(i, 0, v)
#    files_win.refresh()

res = wrapper(main)
#for i in res:
print(res)

