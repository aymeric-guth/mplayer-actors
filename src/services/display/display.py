from rich.console import Console

from ..base import Actor, Message, Sig, actor_system
from . import helpers


class Display(Actor):
    def __init__(self, pid: int, name='',parent: Actor=None) -> None:
        super().__init__(pid, name, parent)
        self.DEBUG = 0

    def dispatch(self, sender: Actor, msg: Message) -> None:
        disp = helpers._disp(Console())
        match msg.sig:
            case Sig.INIT:
                ...
            
            case Sig.REFRESH:
                actor_system.send('Files', Message(sig=Sig.CWD_GET))

            case Sig.CWD_GET:
                dir_list, files_list = msg.args.get('dir_list'), msg.args.get('files_list')
                (display_mode, term_blank, display_width) = helpers.get_term_dimensions(dir_list, files_list)
                (str_object, padding, blank) = helpers.string_format(dir_list, files_list, display_width)
                disp(display_mode, term_blank, str_object, padding, blank)

            case Sig.ERROR:
                print('=' * 100)
                print(msg.args)
                print('=' * 100)

            case _:
                raise SystemExit(f'{msg=}')
