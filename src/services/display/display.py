from cmd import PROMPT
import curses
from typing import Any
from pathlib import Path
from signal import signal, SIGWINCH


from ..base import Actor, Message, Sig, actor_system
from . import helpers

from ...wcurses import stdscr, draw_popup, draw_overlay

from .constants import CMD_HEIGHT, PLAYBACK_HEIGHT
from curses import initscr, endwin


def resize_handler(signum, frame):
    endwin()  # This could lead to crashes according to below comment
    stdscr.refresh()
    actor_system.send('Display', Message(sig=Sig.RESIZE))


signal(SIGWINCH, resize_handler)


class MediaMeta:
    def __init__(self) -> None:
        self.LOG = 0
        self.state = 0
        self.file: str = ''
        self.pos: tuple[int, int] = (0, 0)
        self.volume = 0
        self.playback = 0


class Display(Actor):
    def __init__(self, pid: int, name='',parent: Actor|None=None, **kwargs) -> None:
        super().__init__(pid, name, parent, **kwargs)
        self.LOG = 0
        self.files_overlay = 1
        self.playback_overlay = 0
        self.cmd_overlay = 0
        self.cmd_buff: list[str] = []
        self.files_buff: list[Any] = []
        # self.media_meta = MediaMeta()
        self.media_meta: dict[str, Any] = {}

    def dispatch(self, sender: Actor, msg: Message) -> None:
        match msg:
            case Message(sig=Sig.RESIZE, args=args):
                self.post(self, Message(sig=Sig.DRAW_SCREEN))

            case Message(sig=Sig.CWD_GET, args=args):
                dir_list, files_list = args.get('dir_list'), args.get('files_list')
                self.files_buff = [dir_list, files_list]
                self.post(self, Message(sig=Sig.DRAW_SCREEN))

            case Message(sig=Sig.PROMPT, args=args) if isinstance(args, int):
                # initialisation de la fenetre du prompt
                self.cmd_overlay = args
                if not self.cmd_overlay:
                    self.cmd_buff.clear()
                    curses.curs_set(0)
                self.post(self, Message(sig=Sig.DRAW_SCREEN))

            case Message(sig=Sig.PROMPT, args=args) if isinstance(args, list):
                self.cmd_buff = args.copy()
                self.post(self, Message(sig=Sig.DRAW_SCREEN))

            case Message(sig=Sig.MEDIA_META, args=args):
                k, v = [i for i in args.items()][0]
                self.media_meta.update({k: v})
                if self.playback_overlay:
                    self.post(self, Message(sig=Sig.DRAW_SCREEN))

            case Message(sig=Sig.DRAW_SCREEN):
                # self.post(self, {'type': 'publish'})
                max_height, max_width = stdscr.getmaxyx()
                max_height -= 1
                self.log_msg(f'{max_height=} {max_width=}')
                if self.cmd_overlay:
                    cmd_width = max_width
                    cmd_height = CMD_HEIGHT
                else:
                    cmd_width = 0
                    cmd_height = 0

                if self.playback_overlay:
                    playback_width = max_width
                    playback_height = PLAYBACK_HEIGHT
                else:
                    playback_width = 0
                    playback_height = 0

                if self.files_overlay:
                    files_width = max_width
                    files_height = max_height - cmd_height - playback_height
                else:
                    files_width = 0
                    files_height = 0

                files_x_ofst = 0
                files_y_ofst = 0
                playback_x_ofst = 0
                playback_y_ofst = files_height
                cmd_x_ofst = 0
                cmd_y_ofst = files_height + playback_height

                # self.log_msg(f'{files_height=} {files_width=} {files_y_ofst=} {files_x_ofst=}')
                # self.log_msg(f'{playback_height=} {playback_width=} {playback_y_ofst=} {playback_x_ofst=}')
                # self.log_msg(f'{cmd_height=} {cmd_width=} {cmd_y_ofst=} {cmd_x_ofst=}')
                helpers.draw_files(self, files_height, files_width, files_y_ofst, files_x_ofst)
                helpers.draw_playback(self, playback_height, playback_width, playback_y_ofst, playback_x_ofst)
                helpers.draw_cmd(self, cmd_height, cmd_width, cmd_y_ofst, cmd_x_ofst)
                curses.doupdate()

            case Message(sig=Sig.PLAYBACK_OVERLAY, args=args):
                self.playback_overlay = not self.playback_overlay
                self.post(self, Message(sig=Sig.DRAW_SCREEN))

            case Message(sig=Sig.POPUP, args=args):
                draw_popup(args)

            case Message(sig=Sig.PLAY):
                ...
                # val = msg.args.split('/')[-1]
                # draw_overlay(val)

            case Message(sig=Sig.ERROR, args=args):
                ...
                # actor_system.send('Display', Message(Sig.LOGS, args))

            case Message(sig=Sig.POISON, args=args):
                raise Exception(f'{msg!r}')

            case Message(sig=Sig.AUDIT, args=rid):
                actor_system.send(sender, {'event': 'audit', 'rid': rid, 'data': self.introspect()})

            case {'type': 'subscribe'}:
                self.subscribers.append(sender)

            case {'type': 'publish'}:
                for a in self.subscribers:
                    actor_system.send(a, {'type': 'publish', 'args': self.introspect()})

            case _:
                raise SystemExit(f'{msg=}')

    def terminate(self) -> None:
        ...

    def introspect(self) -> dict[Any, Any]:
        return {
            'actor': repr(self),
            'log': self.LOG,
            'data': {
                'files_overlay': self.files_overlay,
                'playback_overlay': self.playback_overlay,
                'cmd_overlay': self.cmd_overlay,
                'cmd_buff': self.cmd_buff.copy(),
                'files_buff': self.files_buff.copy(),
                'media_meta': self.media_meta.copy(),
            }
        }.copy()
