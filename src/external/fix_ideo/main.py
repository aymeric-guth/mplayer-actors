from . import character_encoding as ce


def display_len(s: str) -> int:
        offset = 0
        for s in s:
            if s in ce.modifier:
                offset -= 1
            elif s in ce.full_width:
                offset += 1
        return len(s) + offset


class StrIdeo:
    def __init__(self, s: str) -> None:
        self.s = s

        self.is_ideo = len(set(s) & ce.global_ideographic) > 0
        if self.is_ideo:
            v = self.s[0]
            last = display_len(v)
            self.str_map: tuple[list[str], list[int]] = ( [v,], [last,] )
            for v in self.s[1:]:
                self.str_map[0].append(v)
                current = display_len(v)
                self.str_map[1].append(last+current)
                last += current

    def __bool__(self) -> bool:
        return self.is_ideo

    def __len__(self) -> int:
        return display_len(self.s)

    def __str__(self) -> str:
        return self.s

    def __getitem__(self, value: int|slice) -> str:
        if not self.__bool__():
            return self.s[value]
        assert isinstance(value, slice), (f'{value=} {self.s=}')
        sentinel = value.stop if value.stop >= 0 else value.stop + len(self)
        for i, v in enumerate(self.str_map[1]):
            if v > sentinel:
                return ''.join(self.str_map[0][:i])
        else:
            return self.s
