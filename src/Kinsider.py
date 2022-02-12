#!/usr/bin/env python3
import asyncio, ssl, re, urllib, time, os, curses, math, sys
import clipboard, shutil
from aiohttp import ClientSession


ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
MAX_CONCURENT_DL = 5

class DataStructure(object):
    def __init__(self, url):
        self.url = url
        self.temp = ''
        self.planner = {}
        if result := re.search(r'(https://downloads.khinsider.com)(/game-soundtracks/album/.*)', self.url):
            self.base_url, self.path_url = result.group(1), result.group(2)
            html = urllib.request.urlopen(url, context=ctx).read().decode('utf8')
            self.album_name = re.search(rf'Album name: <b>(.*)</b><br>', html).group(1)
            regex = rf'<td class="clickable-row"><a href="{self.path_url}(.*\.mp3)">(.*)</a></td>'
            self.files = { v[1]: {'file_path': v[0], 'indice': i, 'download_url': ''} for i, v in enumerate( re.findall(regex, html) ) }
        else:
            sys.exit(0)

class Display(object):
    def __init__(self, dl_list):
        Y = curses.LINES
        X = curses.COLS
        self.size_y = 4
        self.size_x = int( self.size_y * 5 )
        self.blank = ' ' * (self.size_x - 2)
        #size_x = int( size_y * 3.8 )
        buffer_y = 0+5
        buffer_x = 0
        self.dl_list = dl_list
        # Generates all display-cells template
        self.obj_coordonees = {
            self.dl_list.files[file]['indice']: {
                'file_name': file,
                'obj': '',
                'percent': '0%',
                'speed': '0Kb/s',
                'ETA': '???',
                'total_time': '???',
            }
            for file in self.dl_list.files
        }
        # Generates Main cell
        self.main_cell = {
            'album_name': dl_list.album_name,
            'total_completion': '',
            'total_speed': '???',
            'total_time': '???',
            'obj': ''
            }
        self.main_cell['obj'] = curses.newwin(5, X, 0, 0)
        self.main_cell['obj'].box()
        self.main_cell['obj'].addstr(1, 1, f"Album Name : {self.main_cell['album_name']}")
        self.main_cell['obj'].addstr(2, 1, f"Total Speed : {self.main_cell['total_speed']}")
        self.main_cell['obj'].addstr(3, 1, f"Total Time : {self.main_cell['total_time']}")
        self.main_cell['obj'].noutrefresh()

        # Generates all display cells
        for i in range(0, len(self.obj_coordonees)):
            if (buffer_y + self.size_y > Y) and (buffer_x + self.size_x < X):
                buffer_x += self.size_x
                buffer_y = 0+5
            self.obj_coordonees[i]['obj'] = curses.newwin(self.size_y, self.size_x, buffer_y, buffer_x)
            self.obj_coordonees[i]['obj'].box()
            if len(self.obj_coordonees[i]['file_name']) > self.size_x - 2:
                self.obj_coordonees[i]['obj'].addstr(1, 1, self.obj_coordonees[i]['file_name'][:self.size_x-2])
            else:
                self.obj_coordonees[i]['obj'].addstr(1, 1, self.obj_coordonees[i]['file_name'])
            self.obj_coordonees[i]['obj'].addstr(0, 1, f'{i+1}/{len(self.obj_coordonees)}')
            self.obj_coordonees[i]['obj'].addstr(0, self.size_x-3, '0%')
            self.obj_coordonees[i]['obj'].addstr(2, 1, '???')
            self.obj_coordonees[i]['obj'].addstr(2, self.size_x-4, '???')
            self.obj_coordonees[i]['obj'].noutrefresh()
            buffer_y += self.size_y
        curses.doupdate()

    def update_cell(self, file, **kwargs):
        cell_id = self.dl_list.files[file]['indice']
        self.obj_coordonees[cell_id]['percent'] = kwargs.get('percent')
        self.obj_coordonees[cell_id]['speed'] = kwargs.get('speed') + 'b/s'
        self.obj_coordonees[cell_id]['ETA'] = kwargs.get('remaining')
        # Blank variable values: speed, percent, ETA
        for i in range(2, self.size_y-1):
            self.obj_coordonees[cell_id]['obj'].addstr(i, 1, self.blank)
        # update speed
        offset_speed = self.size_x - len(self.obj_coordonees[cell_id]['speed']) - 1
        self.obj_coordonees[cell_id]['obj'].addstr(2, offset_speed, self.obj_coordonees[cell_id]['speed'])
        # update percent
        offset_percent = self.size_x - len(self.obj_coordonees[cell_id]['percent']) - 1
        self.obj_coordonees[cell_id]['obj'].addstr(0, offset_percent, self.obj_coordonees[cell_id]['percent'])
        # update ETA
        self.obj_coordonees[cell_id]['obj'].addstr(2, 1, f"ETA: {self.obj_coordonees[cell_id]['ETA']}")
        self.obj_coordonees[cell_id]['obj'].noutrefresh()
        curses.doupdate()

    def update_cell_done(self, file, **kwargs):
        cell_id = self.dl_list.files[file]['indice']
        self.obj_coordonees[cell_id]['total_time'] = kwargs.get('total_time')
        # Blank non-needed values speed, ETA
        for i in range(2, self.size_y-1):
            self.obj_coordonees[cell_id]['obj'].addstr(i, 1, self.blank)
        # update percent
        self.obj_coordonees[cell_id]['obj'].addstr(0, self.size_x-5, '100%')
        # add total time
        self.obj_coordonees[cell_id]['obj'].addstr(2, 1, self.obj_coordonees[cell_id]['total_time'])
        self.obj_coordonees[cell_id]['obj'].noutrefresh()
        curses.doupdate()

async def request_download_url(dl_list, file):
    async with ClientSession() as session:
        async with session.get(dl_list.url + dl_list.files[file]['file_path'], ssl_context=ctx) as response:
            response = await response.read()
            regex = r'	<p><a style="color: #21363f;" href="(.*)"><span class="songDownloadLink"><i class="material-icons">get_app</i>Click here to download as MP3</span></a></b>'
            dl_list.files[file]['download_url'] = re.search(regex, response.decode('utf8')).group(1)

async def download_files(win, dl_list, queue):
    file = queue
    process = await asyncio.create_subprocess_exec('wget', *('--content-disposition', f'{dl_list.files[file]["download_url"]}'), stderr=asyncio.subprocess.PIPE)
    while True:
        s = await process.stderr.readline()
        s = s.rstrip().decode('utf8')
        if result := re.search(r'\d{1,5}K(\s\.{10}){5}\s{1,2}(\d{1,3}\%)\s{2}(\d{1,5}K|M)\s(\d{1,5}s)', s):
            kwargs = {
                'percent': result.group(2),
                'speed': result.group(3),
                'remaining': result.group(4),
            }
            win.update_cell(file, **kwargs)
        elif result := re.search(r'(100\%)\s.*=(.*s)', s):
            kwargs = {
                'total_time': result.group(2),
            }
            win.update_cell_done(file, **kwargs)
            break

def select_dir(album_name):
    os.chdir(os.getenv('HOME') + '/Downloads')
    try:
        os.mkdir(album_name)
    except FileExistsError:
        shutil.rmtree(album_name, ignore_errors=False, onerror=None)
        os.mkdir(album_name)
    os.chdir(os.getenv('HOME') + '/Downloads/' + album_name)

async def main():
    tasks = ( request_download_url(dl_list, i) for i in dl_list.files )
    await asyncio.gather(*tasks)
    select_dir(dl_list.album_name)
    tasks = set()
    for i in dl_list.files:
        if len(tasks) >= MAX_CONCURENT_DL:
            _done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        tasks.add(asyncio.create_task(
            download_files(win, dl_list, i)
        ))
    await asyncio.wait(tasks)

try:
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    if curses.has_colors():
        curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)

    url = clipboard.paste()
    base_url = "https://downloads.khinsider.com/game-soundtracks/album/"
    if url[:55] != base_url or len(url) <= 55:
        print(f"Invalid URL: {url}")
        time.sleep(3)
        sys.exit(0)
    dl_list = DataStructure(url)
    win = Display(dl_list)
    asyncio.run(main(), debug=True)

finally:
    curses.nocbreak()
    curses.echo()
    curses.curs_set(1)
    curses.endwin()
