from rich.console import Console

from ..base import Actor, Message, Sig
from . import helpers


class Display(Actor):
    def __init__(self, dispatcher: Actor) -> None:
        super().__init__()
        self.dispatcher = dispatcher
        self.DEBUG = 0

    def run(self) -> None:
        disp = helpers._disp(Console())
        while 1:
            (actor, msg) = self.mq.get()
            self.debug(msg, actor)

            match msg.sig:
                case Sig.INIT:
                    ...
                
                case Sig.REFRESH:
                    actor = self.get_actor('Files')
                    actor.post(self, Message(sig=Sig.CWD_GET))

                case Sig.CWD_GET:
                    dir_list, files_list = msg.args.get('dir_list'), msg.args.get('files_list')
                    (display_mode, term_blank, display_width) = helpers.get_term_dimensions(dir_list, files_list)
                    (str_object, padding, blank) = helpers.string_format(dir_list, files_list, display_width)
                    disp(display_mode, term_blank, str_object, padding, blank)

                case Sig.ERROR:
                    print('=' * 100)
                    print(msg.args)
                    print('=' * 100)

                case Sig.REGISTER:
                    self.register(actor)

                case _:
                    raise SystemExit(f'{msg=}')
