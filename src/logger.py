import asyncio
import socket


async def handle_client(
    reader: asyncio.StreamReader, 
    writer: asyncio.StreamWriter
) -> None:
    print('New connection')
    while 1:
        message = await reader.readline()
        print(message.decode('utf-8')[:-1])
        if not message:
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

