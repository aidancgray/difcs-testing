import socket

DST_ADDR = '127.0.0.1'
DST_PORT = 23

SRC_ADDR = '127.0.0.1'
SRC_PORT = 50005

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((SRC_ADDR, SRC_PORT))
s.connect((DST_ADDR, DST_PORT))

print('Telnet opened on port', SRC_PORT)

try:
    while True:
        data, addr = s.recvfrom(1024)
        try:
            data = data.decode('utf-8')
        except UnicodeDecodeError as ex:
            print(ex)
        else:
            print(data) if len(data)>0 else print('--------NULL PACKET--------')
except KeyboardInterrupt as ex:
    print('KeyboardInterrupt')
    s.close()
    print('Telnet closed on port', SRC_PORT)