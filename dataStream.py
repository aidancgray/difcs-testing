import sys
import socket

class dataStream():
    def __init__(self, host, port, delimiter='\n'):
        self.host = host
        self.port = port
        self.delim = delimiter
        self.sock = self.tcp_connect()

        self.__buffer = ''

    def tcp_connect(self):
        connected = False
        port = 9999
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        while not connected:
            s.bind(('127.0.0.1', port))
            try:
                s.connect((self.host, self.port))
            except OSError:
                s.close()
                port-=1
            else:
                connected = True
        print('Telnet opened on port', port)
        return s
    
    def tcp_close(self):
        self.sock.close()
    
    def rdline(self):
        data, addr = self.sock.recvfrom(102)
        try:
            data = data.decode('utf-8')
        except UnicodeDecodeError as ex:
            print(ex)
        else:
            print(f"data->|{data}|<-here") if len(data)>0 else print('----NULL PACKET----')
            return data

    def get_data(self):
        data = self.__buffer

        while True:
            try:
                data_tmp = self.sock.recv(64).decode('utf-8')
            except UnicodeDecodeError as ex:
                print(ex)
            else:
                data = ''.join([data,data_tmp])

                if data_tmp == '' or self.delim in data:
                    break
        
        data_list = data.split(self.delim)
        self.__buffer = self.delim.join(data_list[1:])
        return data_list[0]
    
    def process_data(self, msg_list):
        data = {}
        try:
            if msg_list[0] == 'CNT':
                sin = msg_list[2]
                cos = msg_list[3]
                if msg_list[1] == '1':
                    data["x_sin"] = int(sin)
                    data["x_cos"] = int(cos)
                elif msg_list[1] == '2':
                    data["y_sin"] = int(sin)
                    data["y_cos"] = int(cos)
            
            elif msg_list[0] == 'POS':
                pos = msg_list[2]
                if msg_list[1] == '1':
                    data["x_pos"] = float(pos)
                elif msg_list[1] == '2':
                    data["y_pos"] = float(pos)
            
            elif msg_list[0] == 'OUT':
                sign   = msg_list[2]
                dacVal = msg_list[3]
                if msg_list[1] == '1':
                    data["x_out"] = int(sign+dacVal)
                elif msg_list[1] == '2':
                    data["y_out"] = int(sign+dacVal)
        except IndexError:
            print(msg_list)
        
        return data

if __name__ == "__main__":
    difcs = dataStream('127.0.0.1',23)

    try:
        while True:
            print(difcs.get_data())

    except KeyboardInterrupt:
        sys.exit("\rclosing")
