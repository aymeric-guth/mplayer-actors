import asyncio
import json
from typing import Any
import string
import random


BUFFSIZE = 4096

def serialize(data: dict[str, Any]) -> bytes:
    return _serialize(json.dumps(data).encode('utf-8'))

def _serialize(data: bytes) -> bytes:
    return len(data).to_bytes(length=8, byteorder='big') + data

def deserialize(data: bytes) -> tuple[int, dict[str, Any]]:
    (size, d) = _deserialize(data)
    return (size, json.loads(d.decode("utf-8")))

def _deserialize(data: bytes) -> tuple[int, bytes]:
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


async def _main() -> int:
    reader, writer = await asyncio.open_connection('127.0.0.1', 8081)
    message = {'type': 'subscribe', 'actor': 'Display'}
    
    test = serialize(message)
    writer.write(test)
    await writer.drain()
    try:
        while 1:
            print('client loop')
            header = await reader.readexactly(8)
            size = int.from_bytes(header, byteorder='big')
            data = await reader.readexactly(size)
            resp = json.loads(data.decode("utf-8"))
            print(resp)

            message = {'type': 'acknowledge'}
            writer.write(serialize(message))
            await writer.drain()

    except Exception as err:
        print(err)
    finally:
        writer.close()
        await writer.wait_closed()
        return 0


async def runner():
    tasks = []
    for _ in range(1):
        tasks.append(asyncio.create_task(_main()))
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(runner(), debug=True)
