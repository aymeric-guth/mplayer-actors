from typing import List, Any
import logging
import re

from ..base import Message, Sig, Actor, actor_system
from ... import settings


def eval_cmd(cmd: str) -> tuple[str, Message]:
    # actor_system.send('Logger', Message(Sig.PUSH, f'eval_cmd got new cmd={cmd}'))
    match cmd.split(' '):
        case ['..']:
            # goes back 1 node
            return 'Files', Message(sig=Sig.PATH_SET, args=0)

        case [('root' | 'music' | 'video' | 'td' | 'todo' | 'vdo') as param]:
            # bookmarks
            # goto shortcut dir ~ cd *path argparse(cd *path)
            actor = 'Files'
            message = lambda arg: Message(sig=Sig.PATH_SET, args=arg)

            match param:
                case 'root':
                    return actor, message(settings.ROOT[:])
                case 'music':
                    return actor, message(settings.MUSIC_PATH[:])
                case ('video' | 'vdo'):
                    return actor, message(settings.VIDEO_PATH[:])
                case ('td' | 'todo'):
                    return actor, message(settings.MUSIC_TODO[:])

        case ['reindex']:
            return 'API', Message(sig=Sig.FILES_REINDEX)

        case ['resume']:
            ...

        case['refresh' | 'r']:
            # refresh display, fallback
            return 'Files', Message(sig=Sig.PATH_SET)

        case ['loop' | 'l']:
            # loop mode on / off
            return 'MediaDispatcher', Message(sig=Sig.LOOP)

        case ['quit' | 'q']:
            return 'Dispatcher', Message(sig=Sig.SIGINT)

        case [param] if param.isdigit():
            # basic digit selector
            return 'Files', Message(sig=Sig.PATH_SET, args=int(param))

        case ['stop']:
            return 'MediaDispatcher', Message(sig=Sig.STOP)
            
        case ['play' | 'p', *params]:
            # play parameter
            match params:
                case []:
                    return 'MediaDispatcher', Message(sig=Sig.PLAY_ALL)

                case [param] if param.isdigit():
                    return 'MediaDispatcher', Message(sig=Sig.PLAY_ALL, args=[int(param)])

                case [param1, param2] if param1.isdigit() and param2.isdigit():
                    ...

                case _:
                    ...

        # case ['space']:
        #     return 'MediaDispatcher', Message(sig=Sig.PLAY_PAUSE)

        # case ['next']:
        #     return 'MediaDispatcher', Message(sig=Sig.NEXT)
        
        # case ['previous']:
        #     return 'MediaDispatcher', Message(sig=Sig.PREVIOUS)

        case ['volume' | 'v', value] if value.isdigit():
            # set volume to value
            return 'MediaDispatcher', Message(sig=Sig.VOLUME, args=int(value))

        case ['depth' | 'd', value] if value.isdigit() and int(value) > 0:
            # goes value nodes up
            ...

        case ['open']:
            return 'External', Message(sig=Sig.OPEN)

        case ['?', p] if p:
            return 'Files', Message(sig=Sig.SEARCH, args=p)

        case ['?*', p] if p:
            return 'Files', Message(sig=Sig.SEARCH_ALL, args=p)

        case _:
            return 'Display', Message(sig=Sig.POPUP, args=f'Invalid command: {cmd}')

    return ('Dispatcher', Message(sig=Sig.ERROR))
