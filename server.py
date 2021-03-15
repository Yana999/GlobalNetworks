import socket
import hamming
import sys

import socket
import time

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    host = '192.168.0.102'
    port = 8001


    s.bind((host, port))
    print(f'socket binded to {port}')

    s.listen()

    con, addr = s.accept()

    with con:
        decoder = hamming.Hamming(33)
        while True:

            data = con.recv(50000)
            data = decoder.decode(data.decode())
            if not data:
                break

            con.sendall(data.encode())
        con.close()
        print('Close socket')


