from typing import List, Any


from ...external.actors import Message, Sig, Actor, actor_system

from ...utils import SingletonMeta, clamp


def eval_cmd(cmd: str) -> tuple[str, Message]:
    match cmd.lstrip().rstrip().split(' '):
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
            return 'ActorSystem', Message(sig=Sig.SIGQUIT)

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
                    return 'MediaDispatcher', Message(sig=Sig.PLAY_ALL, args=[int(param1), int(param2)])

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

    return ('ActorSystem', Message(sig=Sig.ERROR))


class CmdCache(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self._container: list[tuple[str, ...]] = []
        self._p = -1

    @property
    def p(self) -> int:        
        return self._p

    @p.setter
    def p(self, value: int) -> None:
        if not len(self._container):
            self._p = -1
        else:
            self._p = int(clamp(0, len(self._container))(value))

    def next(self) -> list[str]:
        self.p += 1
        if not len(self._container):
            return list()
        elif self.p == len(self._container):
            return list()
        else:
            return list(self._container[self.p])

    def prev(self) -> list[str]:
        self.p -= 1
        if not len(self._container):
            return list()
        else:
            return list(self._container[self.p])

    def push(self, value: list[str]) -> None:
        self._container.append(tuple(value))
        self.p = len(self._container)


class CmdBuffer(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self._container: list[str] = []
        self._p = 0

    @property
    def p(self) -> int:
        assert self._p <= len(self._container) and self._p >= 0
        return self._p

    @p.setter
    def p(self, value: int) -> None:
        self._p = value
        assert self._p <= len(self._container) and self._p >= 0

    def insert(self, value: str) -> None:
        self._container.insert(self.p, value)
        self.p += 1
    
    def delete(self, ofst: int=0) -> None:
        if not self._container:
            return
        if not ofst:
            self.p -= 1
            del self._container[self.p]
        else:
            del self._container[self.p]

    def clear(self) -> None:
        self._container.clear()
        self.p = 0


# key left
# key right
# del
# supr
# char
# enter

# [a, b, c]
#  0  1  2
# cur = 3