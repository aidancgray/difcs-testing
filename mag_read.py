import os
import sys
import serial
import socket
from serial.serialutil import EIGHTBITS, PARITY_NONE, STOPBITS_ONE


if os.name == "posix":
    SER_MAG = '/dev/tty.usbserial-B001A17V'
else:
    SER_MAG = 'COM6'

TCP_MAG_HOST = '172.16.2.61'
TCP_MAG_PORT = 8234
MAX_LIST_LEN = 30

class MagSensor():
    def __init__(self, conn, pole_pitch, mode='passive'):
        if len(conn) == 2:
            self.tcp_mag_host, self.tcp_mag_port = conn
            self.sock, self.strm_rdr = self.tcp_connect()
            self.serial_id, self.serial = None, None
        else:
            self.serial_id = conn
            self.serial = self.serial_connect()
            self.tcp_mag_host, self.tcp_mag_port, self.sock, self.strm_rdr = None, None, None, None

        self.pole_pitch = pole_pitch    # mm
        self.mode = mode                # active / passive

    def tcp_connect(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.tcp_mag_host, self.tcp_mag_port))
        strm_rdr = socket.SocketIO(s,'r')
        return s, strm_rdr
    
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

    def ena_PID(self, channel):
        msg = f'~D0,enaPID,{channel}\n'
        resp = self.serial_send(msg)
        return resp
    
    def dis_PID(self, channel):
        msg = f'~D0,disPID,{channel}\n'
        resp = self.serial_send(msg)
        return resp
    
    def set_op(self, channel, output):
        msg = f'~D0,sManOP,{channel},{output}\n'
        resp = self.serial_send(msg)
        return resp
    
    def set_ChMode(self, channel, mode):
        msg = f'~D0,sChMode,{channel},{mode}\n'
        resp = self.serial_send(msg)
        return resp
    
    def set_sp(self, channel, setpoint):
        msg = f'~D0,sSP,{channel},{setpoint}\n'
        resp = self.serial_send(msg)
        return resp

    def get_PID(self, channel,value):
        msg = f'~D0,gPID,{channel},{value}\n'
        resp = self.serial_send(msg)
        difcs_id, channel, term, status = resp
        return float(term)
    
    def get_CV(self, channel):
        msg = f'~D0,gPIDdata,{channel},CV\n'
        resp = self.serial_send(msg)
        difcs_id, channel, cv, status = resp
        return float(cv)
    
    def get_IPreal(self, channel):
        msg = f'~D0,gIPdata,{channel},real\n'
        resp = self.serial_send(msg)
        difcs_id, channel, pos, status = resp
        return float(pos)
    
    def get_counts(self):
        data = [[None,None],[None,None]]

        while None in data[0] or None in data[1]:
            if self.serial:
                msg = self.serial.readline().decode()
            else:
                msg = ' '
                while msg[0] != 'D':
                    msg = self.strm_rdr.readline().decode('utf-8')
                
            msg_list = msg.split(',')

            if len(msg_list) == 5:
                difcs_id, channel, sin, cos, status = msg_list
                if channel == '1':
                    data[0][0] = int(sin)
                    data[0][1] = int(cos)
                elif channel == '2':
                    data[1][0] = int(sin)
                    data[1][1] = int(cos)
                
        return data
    
    def get_real_position(self):
        data = [None,None]

        while None in data:
            try:
                if self.serial:
                    msg = self.serial.readline().decode()
                else:
                    msg = ' '
                    while msg[0] != 'D':
                        msg = self.strm_rdr.readline().decode('utf-8')
            except UnicodeDecodeError:
                print('UnicodeDecodeError - Trying again')
            else:    
                msg_list = msg.split(',')
    
                if len(msg_list) == 4:
                    difcs_id, channel, pos, status = msg_list
                    if channel == '1':
                        data[0] = float(pos)
                    elif channel == '2':
                        data[1] = float(pos)
                
        return data

if __name__ == "__main__":
    mag = MagSensor(SER_MAG, 1, 'passive')

    try:
        while True:
            # count_data = mag.get_counts()
            # print(f'xs={count_data[0][0]}, xc={count_data[0][1]}')
            # print(f'ys={count_data[1][0]}, yc={count_data[1][1]}')
            pos_data = mag.get_real_position()
            print(f'xpos={pos_data[0]}, ypos={pos_data[1]}')
    except KeyboardInterrupt:
        sys.exit("\rclosing")