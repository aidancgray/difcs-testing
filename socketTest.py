import socket

remote_host = '127.0.0.1'
remote_port = 23

local_host = '127.0.0.1'
local_port = 9999

with socket.socket() as s:
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    connected = False
    while not connected:
        s.bind((local_host,local_port))
        try:
            s.connect((remote_host,remote_port))
        except OSError:
            s.close()
            local_port-=1
        else:
            connected = True
    print('Telnet opened on port',local_port)

    data, addr = s.recvfrom(102)
    try:
        data = data.decode('utf-8')
    except UnicodeDecodeError as ex:
        print(ex)
    else:
        print(f"-DATA BELOW-\n{data}\n-DATA ABOVE-") if len(data)>0 else print('---EMPTY PACKET---')