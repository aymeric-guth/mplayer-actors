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
        print(f'prev call {self.p=}')
        if self.p > 0:
            self.p -= 1
            print(f'prev branch {self.p=}')
        return self.container[self.p]
    
    def next(self) -> str:
        if self.p >= len(self.container) - 1:
            return None
        else:
            self.p += 1
            return self.container[self.p]

# creation de la playlist 6 elements
# next renvoi element 0
# prev renvoi element 0

# next renvoi element 1
# prev renvoi element 0

# next renvoi element 1
# next renvoi element 2
# next renvoi element 3
# prev renvoi element 2

# next renvoi element 3
# next renvoi element 4
# next renvoi element 5
# next renvoi None

# prev renvoi element 5
# next renvoi None