import asyncio
import json
from typing import Any
import string
import random


BUFFSIZE = 4096

# def serialize(data: dict[str, Any]) -> bytes:
#     return json.dumps(data).encode('utf-8')


# def deserialize(data: bytes) -> dict[str, Any]:
#     return json.loads(data.decode("utf-8"))

def serialize(data: bytes) -> bytes:
    return len(data).to_bytes(length=8, byteorder='big') + data

def deserialize(data: bytes) -> tuple[int, bytes]:
    return (int.from_bytes(data[:8], byteorder='big'), data[8:])

def random_str(n: int) -> bytes:
    return (''.join(random.choice(string.ascii_uppercase) for _ in range(n))).encode('utf-8')


async def main() -> int:
    reader, writer = await asyncio.open_connection('127.0.0.1', 8081)
    test = random_str(random.randint(BUFFSIZE, BUFFSIZE*10))
    # test = random_str(10)    
    writer.write(serialize(test))
    # writer.write(b'Hello World')
    await writer.drain()
    data = await reader.readexactly(8 + len(test))
    size, d = deserialize(data)
    assert test == d, print(f'test={test} data={d}')

    writer.close()
    await writer.wait_closed()
    return 0


async def runner():
    tasks = []
    for _ in range(100):
        tasks.append(asyncio.create_task(main()))
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(runner(), debug=True)
    # asyncio.run(main(), debug=True)