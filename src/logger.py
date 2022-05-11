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
            fmt = logging.Formatter(fmt='[%(asctime)s][%(levelname)s][%(actor)s][%(name)s:%(lineno)s][%(message)s]')
            # fmt = logging.Formatter(fmt='[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)s][%(funcName)s][%(message)s]')
            print(fmt.format(record))
            # print(pickle.loads(message))

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



{
    'name': 'src.services.mpv.main', 
    'msg': "msg=Message(sig=Sig.MPV_EVENT, args=<class 'src.services.mpv.main.MpvEvent'>)", 
    'args': None, 
    'levelname': 'INFO', 
    'levelno': 20, 
    'pathname': '/Users/yul/Desktop/Network/mplayer/src/services/mpv/main.py', 
    'filename': 'main.py', 
    'module': 'main', 
    'exc_info': None, 
    'exc_text': None, 
    'stack_info': None, 
    'lineno': 173, 
    'funcName': 'dispatch', 
    'created': 1652260813.338169, 
    'msecs': 338.1690979003906, 
    'relativeCreated': 187.9129409790039, 
    'thread': 123145554239488, 
    'threadName': 'Thread-10 (run)', 
    'processName': 'MainProcess', 
    'process': 2263
}

{
    'name': 'src.services.api.api', 
    'msg': "sender=API(pid=3, parent=None, kwargs={}) receiver=API(pid=3, parent=None, kwargs={}) msg=Message(sig=Sig.EXT_SET, args=<class 'NoneType'>)", 
    'args': None, 
    'levelname': 'INFO', 
    'levelno': 20, 
    'pathname': '/Users/yul/Desktop/Network/mplayer/src/services/api/api.py', 
    'filename': 'api.py', 
    'module': 'api', 
    'exc_info': None, 
    'exc_text': None, 
    'stack_info': None, 
    'lineno': 27, 
    'funcName': 'dispatch', 
    'created': 1652261235.015935, 
    'msecs': 15.934944152832031, 
    'relativeCreated': 493.53504180908203, 
    'thread': 123145406058496, 
    'threadName': 'Thread-3 (run)', 
    'processName': 'MainProcess', 
    'process': 2451
}
'[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)s][%(funcName)s][%(message)s]'


# logs:
#     nom_actor (class, pid, )
#     namespace fichier
#     ligne
#     loglevel

# '[%(asctime)s][%(levelname)s][%(name)s:%(lineno)s][%(funcName)s][%(message)s]'