import asyncio
import json
from typing import Any


BUFFSIZE = 4096

def serialize(data: dict[str, Any]) -> bytes:
    return json.dumps(data).encode('utf-8')


def deserialize(data: bytes) -> dict[str, Any]:
    return json.loads(data.decode("utf-8"))


async def main() -> None:
    reader, writer = await asyncio.open_connection('127.0.0.1', 8081)
    writer.write(serialize({'cmd': 'audit', 'actor': 'Display'}))
    await writer.drain()
    data = await reader.readline()
    print(f'Got response: {deserialize(data)}')

    writer.close()
    await writer.wait_closed()
    


if __name__ == '__main__':
    asyncio.run(main(), debug=True)
