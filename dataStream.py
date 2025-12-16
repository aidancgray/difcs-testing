import os
import sys
import serial
import socket
from serial.serialutil import EIGHTBITS, PARITY_NONE, STOPBITS_ONE

if os.name == 'posix':
    SER_MAG = '/dev/tty.usbserial-B001A17V'

else:
    SER_MAG = 'COM3'

MAX_LIST_LEN = 30

class DataStream():
    def __init__(self, conn, delimiter='\n'):
        if len(conn) == 2:
            self.host, self.port = conn
            self.sock = self.tcp_connect()
            self.serial_id, self.serial = None, None
        else:
            self.serial_id = conn
            self.serial = self.serial_connect()
            self.host, self.port, self.sock = None, None, None
        
        self.delim = delimiter
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

    def serial_connect(self):
        ser_mag = serial.Serial(port=self.serial_id,
                                baudrate=128000,
                                timeout=1,
                                bytesize=EIGHTBITS,
                                parity=PARITY_NONE,
                                stopbits=STOPBITS_ONE)
        ser_mag.reset_input_buffer()
        return ser_mag

    def serial_send(self, msg):
        self.serial.write(msg.encode('utf-8'))
        rcv = '\0'
        while rcv[0] != "$":
            rcv = self.serial.readline().decode()
        rcv_list = rcv.split(',')
        return rcv_list

    def serial_get_data(self, counts=True, pos=True, out=True):
        data = {}
        data["x_sin"] = None if counts else 0
        data["x_cos"] = None if counts else 0
        data["y_sin"] = None if counts else 0
        data["y_cos"] = None if counts else 0
        data["x_pos"] = None if pos else 0
        data["y_pos"] = None if pos else 0
        data["x_out"] = None if out else 0
        data["y_out"] = None if out else 0

        while None in data.values():
            rd_line = self.serial.readline()
            try:
                msg_list = rd_line.decode().split(',')
            except UnicodeDecodeError:
                print(rd_line)
            else:
                try:
                    if msg_list[0] == 'CNT' and counts:
                        sin = msg_list[2]
                        cos = msg_list[3]
                        if msg_list[1] == '1':
                            data["x_sin"] = int(sin)
                            data["x_cos"] = int(cos)
                        elif msg_list[1] == '2':
                            data["y_sin"] = int(sin)
                            data["y_cos"] = int(cos)
                    
                    elif msg_list[0] == 'POS' and pos:
                        pos = msg_list[2]
                        if msg_list[1] == '1':
                            data["x_pos"] = float(pos)
                        elif msg_list[1] == '2':
                            data["y_pos"] = float(pos)
                    
                    elif msg_list[0] == 'OUT' and out:
                        sign   = msg_list[2]
                        dacVal = msg_list[3]
                        if msg_list[1] == '1':
                            data["x_out"] = int(sign+dacVal)
                        elif msg_list[1] == '2':
                            data["y_out"] = int(sign+dacVal)
                except IndexError:
                    print(msg_list)
        
        return data

    def tcp_read_data(self):
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
    
    # Always call get_data(), which checks if TCP or SERIAL should be used
    def get_data(self):
        if self.sock:
            data = {}
            while ('x_pos' not in data) or ('y_pos' not in data):
                raw_data = self.tcp_read_data()
                data_tmp = self.process_data(raw_data)
                data.update(data_tmp) if data_tmp else None
        elif self.serial:
            data = self.serial_get_data()
        else:
            return None
        return data

if __name__ == "__main__":
    difcs_tcp = DataStream(('127.0.0.1',23))
    # difcs_serial = DataStream(SER_MAG)

    try:
        while True:
            data_tcp = difcs_tcp.get_data()
            if data_tcp:
                for key in data_tcp:
                    print(f'{key}={data_tcp[key]}')
            
            # data_serial = difcs_serial.get_data()
            # if data_serial:
                # for key in data_serial:
                    # print(f'{key}={data_serial[key]}')

    except KeyboardInterrupt:
        sys.exit("\rclosing")
