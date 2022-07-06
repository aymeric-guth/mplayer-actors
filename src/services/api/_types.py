from typing import Any
import dataclasses
import json


@dataclasses.dataclass(frozen=True)
class FileEntry:
    path: str
    filename: str
    extension: str

    def to_json(self) -> dict[str, str]:
        return dataclasses.asdict(self)

    @classmethod
    def from_array(cls, params: list[str]) -> Any:
        return FileEntry(
            path=params[0],
            filename=params[1],
            extension=params[2],
        )
