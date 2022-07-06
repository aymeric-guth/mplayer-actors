import asyncio
import socket
import pickle
import logging


async def handle_client(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> None:
    print("New connection")
    while 1:
        try:
            try:
                header = await reader.readexactly(4)
            except asyncio.IncompleteReadError:
                raise

            size = int.from_bytes(header, byteorder="big")
            if not size:
                raise Exception

            message = await reader.readexactly(size)
            record = logging.makeLogRecord(pickle.loads(message))
            fmt = logging.Formatter(
                fmt="[%(asctime)s][%(levelname)s][%(actor)s][%(name)s:%(lineno)s]\n[%(message)s]\n"
            )
            print(fmt.format(record))

        except Exception:
            writer.close()
            await writer.wait_closed()
            print("Client terminated")
            return


async def main() -> None:
    #    server = await asyncio.start_server(handle_client, "192.168.1.100", 8080)
    server = await asyncio.start_server(handle_client, "127.0.0.1", 8080)
    async with server:
        try:
            await server.serve_forever()
        except Exception as e:
            ...


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
