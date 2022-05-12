from collections import deque


class Playlist:
    def __init__(self, items: list[str]) -> None:
        if items is None:
            raise Exception
        self.container = items[:]
        self.p = -1

    def __bool__(self) -> bool:
        return self.p < len(self.container) - 1

    def __len__(self) -> int:
        return len(self.container)
    
    def prev(self) -> str:
        if self.p > 0:
            self.p -= 1
        return self.container[self.p]
    
    def next(self) -> str|None:
        if self.p >= len(self.container) - 1:
            return None
        else:
            self.p += 1
            return self.container[self.p]

    def pos(self) -> tuple[int, int]:
        return (self.p + 1, len(self.container))

    def clear(self) -> None:
        self.container = []
        self.p = -1
