from typing import List, Any

from ..base import Message, Sig, Actor, actor_system


def eval_cmd(cmd: str) -> tuple[str, Message]:
    match cmd.split(' '):
        case ['..']:
            # goes back 1 node
            return 'Files', Message(sig=Sig.PATH_SET, args=0)

        case ['h' | 'hook', label]:
            # bookmarks
            # hooks cwd and maps it to label
            return 'External', Message(sig=Sig.HOOK, args=label)

        case ['j' | 'jump', label]:
            # bookmarks
            # jumps to corresponding directory
            return 'External', Message(sig=Sig.JUMP, args=label)

        case ['reindex']:
            return 'API', Message(sig=Sig.FILES_REINDEX)

        case ['resume']:
            ...

        case['refresh' | 'r']:
            # refresh display, fallback
            return 'Files', Message(sig=Sig.PATH_SET)

        case ['loop' | 'l', param] if param.isdigit():
            # loop mode on / off
            return 'MediaDispatcher', Message(sig=Sig.PLAYBACK_MODE, args=int(param))

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
