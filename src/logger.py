import asyncio
import socket
import pickle
import logging


async def handle_client(
    reader: asyncio.StreamReader, 
    writer: asyncio.StreamWriter
) -> None:
    print('New connection')
    while 1:
        try:
            try:
                header = await reader.readexactly(4)
            except asyncio.IncompleteReadError:
                raise

            size = int.from_bytes(header, byteorder='big')
            if not size:
                raise Exception

            message = await reader.readexactly(size)
            record = logging.makeLogRecord(pickle.loads(message))
            fmt = logging.Formatter(fmt='[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)s][%(funcName)s][%(message)s]')
            print(fmt.format(record))

        except Exception:
            writer.close()
            await writer.wait_closed()
            print('Client terminated')
            return


async def main() -> None:
    server = await asyncio.start_server(handle_client, "127.0.0.1", 8080)
    async with server:
        try:
            await server.serve_forever()
        except Exception as e:
            ...


if __name__ == '__main__':
    asyncio.run(main(), debug=True)


# initialisation
# addr = socket.getaddrinfo("127.0.0.1", 8080)[0][-1]
# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.setblocking(True)
# sock.bind(addr)
# sock.listen(5)

# # handle new client connection
# while 1:
#     conn, addr = sock.accept()
#     while 1:
#         conn.settimeout(0)
#         data = conn.recv()
#         if not data:
#             print('Client terminated')
#             break
#         else:
#             print(data.decode('utf-8'))

#     conn.close()



b'\x00\x00\x02\x04}q\x00(X\x04\x00\x00\x00nameq\x01X\x08\x00\x00\x00__main__q\x02X\x03\x00\x00\x00msgq\x03X\x03\x00\x00\x00lolq\x04X\x04\x00\x00\x00argsq\x05NX\t\x00\x00\x00levelnameq\x06X\x04\x00\x00\x00INFOq\x07X\x07\x00\x00\x00levelnoq\x08K\x14X\x08\x00\x00\x00pathnameq\tX5\x00\x00\x00/Users/yul/Desktop/Network/mplayer/essais/sock/log.pyq\nX\x08\x00\x00\x00filenameq\x0bX\x06\x00\x00\x00log.pyq\x0cX\x06\x00\x00\x00moduleq\rX\x03\x00\x00\x00logq\x0eX\x08\x00\x00\x00exc_infoq\x0fNX\x08\x00\x00\x00exc_textq\x10NX\n\x00\x00\x00stack_infoq\x11NX\x06\x00\x00\x00linenoq\x12K\x10X\x08\x00\x00\x00funcNameq\x13X\x08\x00\x00\x00<module>q\x14X\x07\x00\x00\x00createdq\x15GA\xd8\x9e\xb54\x97U?X\x05\x00\x00\x00msecsq\x16G@v\xc9?\x86\x00\x00\x00X\x0f\x00\x00\x00relativeCreatedq\x17G@!\x7f\xfb\x00\x00\x00\x00X\x06\x00\x00\x00threadq\x18L4675089856L\nX\n\x00\x00\x00threadNameq\x19X\n\x00\x00\x00MainThreadq\x1aX\x0b\x00\x00\x00processNameq\x1bX\x0b\x00\x00\x00MainProcessq\x1cX\x07\x00\x00\x00processq\x1dM\xfc\x10u.'