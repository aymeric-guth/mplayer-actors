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


async def _main(message: str) -> int:
    reader, writer = await asyncio.open_connection('127.0.0.1', 8081)
    writer.write(message.encode('utf-8'))
    await writer.drain()
    # data = await reader.readline()
    data = await reader.read(BUFFSIZE)
    print(f'Got response: {data.decode("utf-8")}')

    writer.close()
    await writer.wait_closed()
    return 0


async def __main(actor: str) -> int:
    reader, writer = await asyncio.open_connection('127.0.0.1', 8081)
    writer.write(serialize({'cmd': 'audit', 'actor': actor}))
    await writer.drain()
    data = await reader.readline()
    print(f'Got response: {deserialize(data)}')

    writer.close()
    await writer.wait_closed()
    return 0


async def runner():
    tasks = []
    for _ in range(10):
        tasks.append(asyncio.create_task(__main('Display')))
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(runner(), debug=True)

    # if len(sys.argv) != 2:
    #     raise SystemExit

    # sys.exit(asyncio.run(main(sys.argv[1]), debug=True))
