# import fix_encoding.latin as latin
from . import latin
from . import japanese
from . import merge


def fix(wrapped: list[str]) -> str:
    r: list[str] = []
    for s in wrapped:
        r.append(merge.STANDARD_MAP_STR.get(s, s) )
    return "".join(r)


class Str(object):
    def __init__(self, s: str):
        self.s: str = s
        self.unique_individual_symbols: set[str] = set(s)
        self.STANDARD_MAP_BYTES: dict[bytes, bytes] = merge.STANDARD_MAP_BYTES
        self.STANDARD_MAP_STR: dict[str, str] = merge.STANDARD_MAP_STR
        self.COMBINING_SUPPORTED: set[str] = merge.COMBINING_SUPPORTED
        self.COMBINING_FULL: set[str] = merge.COMBINING_FULL
        self.SUPPORTED_RANGE: set[str] = merge.SUPPORTED_RANGE

        if (self.unique_individual_symbols - (merge.SUPPORTED_RANGE | merge.COMBINING_FULL)):
            ...
            # print(f"Non latin character detected: s={self.s}")
            # raise NotImplementedError("Non latin character detected")

        self.wrapped: list[str] = [ i for i in self ]

    def __iter__(self):
        self.n: int = 0
        self.max = len(self.s)
        return self

    def __next__(self) -> str:
        buffer: list[str] = []
        if self.n >= self.max:
            raise StopIteration
        try:
            buffer.append(self.s[self.n])
            while (self.s[self.n+1] in merge.COMBINING_FULL):
                buffer.append(self.s[self.n+1])
                self.n += 1
        except IndexError:
            pass
        finally:
            self.n += 1
            return "".join(buffer)

    def __len__(self):
        return len(self.wrapped)

    def __getitem__(self, value) -> str:
        return fix(self.wrapped[value])

    def __str__(self) -> str:
        return fix(self.wrapped)

    def unwrap(self) -> str:
        return fix(self.wrapped)
