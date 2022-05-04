import asyncio
import json
from typing import Any
import sys


BUFFSIZE = 4096

def serialize(data: dict[str, Any]) -> bytes:
    return json.dumps(data).encode('utf-8')


def deserialize(data: bytes) -> dict[str, Any]:
    return json.loads(data.decode("utf-8"))


async def main(actor: str) -> int:
    reader, writer = await asyncio.open_connection('127.0.0.1', 8081)
    writer.write(serialize({'cmd': 'audit', 'actor': actor}))
    await writer.drain()
    data = await reader.readline()
    print(f'Got response: {deserialize(data)}')

    writer.close()
    await writer.wait_closed()
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit
    sys.exit(asyncio.run(main(sys.argv[1]), debug=True))
