import sys
import socket

class DataStream():
    def __init__(self, host, port, delimiter='\n'):
        self.host = host
        self.port = port
        self.delim = delimiter
        self.sock = self.tcp_connect()

        self.__buffer = ''

    def tcp_connect(self):
        connected = False
        port = 9999
        
        while not connected:
            s = socket.socket()
            s.settimeout(5)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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

    def read_data(self):
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
    
    def process_data(self, raw_data):
        data = {}
        msg_split = [x for x in raw_data.split(';') if x]

        if len(msg_split) != 3:
            return None

        for msg in msg_split:
            msg_list = [x for x in msg.split(',') if x]
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
    
    def get_data(self):
        data = {}
        while ('x_pos' not in data) or ('y_pos' not in data):
            raw_data = self.read_data()
            data_tmp = self.process_data(raw_data)
            data.update(data_tmp) if data_tmp else None
        return data


if __name__ == "__main__":
    difcs = DataStream('127.0.0.1',23)

    try:
        while True:
            data = difcs.get_data()
            if data:
                for key in data:
                    print(f'{key}={data[key]}')

    except KeyboardInterrupt:
        sys.exit("\rclosing")
