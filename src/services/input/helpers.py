from actors import Message, Sig, Event, Request, Response

from ...utils import SingletonMeta, clamp
from ...strings import ERRORS


def eval_cmd(cmd: str) -> tuple[str, Message|Response|Request|Event]:
    match cmd.lstrip().rstrip().split(' '):
        case ['..']:
            # goes back 1 node
            return 'Files', Message(sig=Sig.PATH_SET, args=0)

        case ['h' | 'hook', label]:
            # bookmarks
            # hooks cwd and maps it to label
            return 'External', Request(type='cmd', name='hook', args=label)

        case ['j' | 'jump', label]:
            # bookmarks
            # jumps to corresponding directory
            return 'External', Request(type='cmd', name='jump', args=label)

        case ['reindex']:
            return 'API', Request(type='api', name='reindex')

        case ['resume']:
            ...

        case['refresh' | 'r']:
            # refresh display, fallback
            return 'Files', Message(sig=Sig.PATH_SET)

        case ['loop' | 'l', param] if param.isdigit():
            # loop mode on / off
            return 'MediaDispatcher', Request(type='player', name='playback-mode', args=int(param))

        case ['quit' | 'q']:
            return 'ActorSystem', Message(sig=Sig.SIGQUIT)

        case ['current']:
            return 'ActorSystem', Message(sig=Sig.SIGQUIT)

        case [param] if param.isdigit():
            # basic digit selector
            return 'Files', Message(sig=Sig.PATH_SET, args=int(param))

        case ['stop']:
            return 'MediaDispatcher', Request(type='player', name='play-stop')
            
        case ['play' | 'p', *params]:
            # play parameter
            match params:
                case []:
                    return 'MediaDispatcher', Request(type='player', name='play-selection')

                case [param] if param.isdigit():
                    return 'MediaDispatcher', Request(type='player', name='play-selection', args=[int(param)])

                case [param1, param2] if param1.isdigit() and param2.isdigit():
                    return 'MediaDispatcher', Request(type='player', name='play-selection', args=[int(param1), int(param2)])

                case _:
                    ...

        case ['volume' | 'v', value] if value.isdigit():
            # set volume to value
            return 'MediaDispatcher', Request(type='player', name='volume', args=value)

        case ['depth' | 'd', value] if value.isdigit() and int(value) > 0:
            # goes value nodes up
            ...

        case ['open']:
            return 'External', Request(type='os', name='open')

        case ['?', p] if p:
            return 'Files', Message(sig=Sig.SEARCH, args=p)

        case ['?*', p] if p:
            return 'Files', Message(sig=Sig.SEARCH_ALL, args=p)

        case ['send', actor, *msg] if actor and msg:
            return actor, Request(type='player', name='play-pause')
        
        case ['login']:
            return 'API', Request(type='api', name='login')

        case ['logs', 'actors']:
            return 'ActorSystem', Message(sig=Sig.PRINT_ALL)

        case ['logs', 'clear']:
            return 'ActorSystem', Message(sig=Sig.CLEAR_SCREEN)

        case ['log', pid, level] if pid.isdigit() and level.isdigit() and int(pid) >= 0:
            # CRITICAL 50 # ERROR 40 # WARNING 30 # INFO 20 # DEBUG 10 # NOTSET 0
            return int(pid), Message(sig=Sig.LOGGING, args=int(level) * 10)

        case _:
            return 'Display', Event(type='error', name='bad-cmd', args=ERRORS.CMD.format(cmd))

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
        self._p = int(clamp(0, len(self._container))(value))
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

    def get(self) -> list[str]:
        return self._container

    def to_str(self) -> str:
        return ''.join(self._container)

    def init(self, value: list[str]) -> None:
        self._container = value
        self.p = len(self._container)

    def mov(self, value: int=0) -> None:
        if value:
            self.p += 1
        else:
            self.p -= 1

    def serialize(self) -> tuple[str, int]:
        return (''.join(self._container), self.p)
