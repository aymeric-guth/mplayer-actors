import select
import socket
import sys
import queue


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(False)
server_address = ('localhost', 10000)
server.bind(server_address)
server.listen(5)

inputs: list[socket.socket] = [ server, ]
outputs: list[socket.socket] = []
message_queues: dict[socket.socket, queue.Queue] = {}


while inputs:
    readable, writable, exceptional = select.select(inputs, outputs, inputs)
    print(f'{readable=}', f'{writable=}', f'{exceptional=}')
    for s in readable:
        if s is server:
            # A "readable" server socket is ready to accept a connection
            connection, client_address = s.accept()
            connection.setblocking(0)
            inputs.append(connection)
            # Give the connection a queue for data we want to send
            message_queues[connection] = queue.Queue()
        else:
            data = s.recv(1024)
            if data:
                message_queues[s].put(data)
                if s not in outputs:
                    outputs.append(s)
            else:
                # Stop listening for input on the connection
                if s in outputs:
                    outputs.remove(s)
                inputs.remove(s)
                s.close()
                # Remove message queue
                del message_queues[s]

    # Handle outputs
    for s in writable:
        try:
            next_msg = message_queues[s].get_nowait()
        except queue.Empty:
            # No messages waiting so stop checking for writability.
            outputs.remove(s)
        else:
            s.send(next_msg)

    # Handle "exceptional conditions"
    for s in exceptional:
        # Stop listening for input on the connection
        inputs.remove(s)
        if s in outputs:
            outputs.remove(s)
        s.close()
        del message_queues[s]
