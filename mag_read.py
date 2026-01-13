import os
import sys
import serial
import socket
from serial.serialutil import EIGHTBITS, PARITY_NONE, STOPBITS_ONE


if os.name == "posix":
    SER_MAG = '/dev/tty.usbserial-B001A17V'
else:
    SER_MAG = 'COM3'

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
                                timeout=3, 
                                bytesize=EIGHTBITS,
                                parity=PARITY_NONE,
                                stopbits=STOPBITS_ONE)
        ser_mag.reset_input_buffer()
        return ser_mag
    
    def serial_send(self, msg):
        self.serial.write(msg.encode('utf-8'))
        rcv = '\0'
        while rcv[0] != "$":
            rcv_raw = self.serial.readline()
            try:
                rcv_tmp = rcv_raw.decode('utf-8')
            except UnicodeDecodeError as ex:
                print(f"{ex}: {rcv_raw}")
                return None
            else:
                rcv = rcv_tmp if len(rcv_tmp)>0 else '\0'
        return rcv
    
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

            if len(msg_list) == 4:
                difcs_id, cmd, channel, sin, cos = msg_list
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
    
                if len(msg_list) == 3:
                    difcs_id, cmd, channel, pos = msg_list
                    if channel == '1':
                        data[0] = float(pos)
                    elif channel == '2':
                        data[1] = float(pos)
                
        return data
    
    def get_data_pid_test(self):
        data = [[None,None],
                [None,None]]

        while (None in data[0]) or (None in data[1]):
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
    
                if len(msg_list) == 3:
                    difcs_id, cmd, channel, pos = msg_list
                    if channel == '1':
                        data[0][0] = float(pos)
                    elif channel == '2':
                        data[1][0] = float(pos)
                elif len(msg_list) == 5:
                    difcs_id, cmd, channel, sign, dacVal = msg_list
                    if cmd == 'OUT':
                        if channel == '1':
                            data[0][1] = int(sign+dacVal)
                        elif channel == '2':
                            data[1][1] = int(sign+dacVal)
                
        return data
    
    def get_difcs_msg(self, counts=True, pos= True, out=True):
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
                    if msg_list[1] == 'CNT' and counts:
                        sin = msg_list[3]
                        cos = msg_list[4]
                        if msg_list[2] == '1':
                            data["x_sin"] = int(sin)
                            data["x_cos"] = int(cos)
                        elif msg_list[2] == '2':
                            data["y_sin"] = int(sin)
                            data["y_cos"] = int(cos)
                    
                    elif msg_list[1] == 'POS' and pos:
                        pos = msg_list[3]
                        if msg_list[2] == '1':
                            data["x_pos"] = float(pos)
                        elif msg_list[2] == '2':
                            data["y_pos"] = float(pos)
                    
                    elif msg_list[1] == 'OUT' and out:
                        sign   = msg_list[3]
                        dacVal = msg_list[4]
                        if msg_list[2] == '1':
                            data["x_out"] = int(sign+dacVal)
                        elif msg_list[2] == '2':
                            data["y_out"] = int(sign+dacVal)
                except IndexError:
                    print(msg_list)
        
        return data
    
    def get_telemetry(self):
        if self.mode == 'passive':
            return self.get_difcs_msg()
        
        cmd = '~D0,gTlm\n'
        resp = self.serial_send(cmd)
        if not resp:
            return None
        resp = resp[4:-8]
        resp_list = [x for x in resp.split(';') if x]

        data = {}
        for msg in resp_list:    
            try:
                msg_list = msg.split(',')
            except UnicodeDecodeError:
                print(msg)
            else:
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
    mag = MagSensor(SER_MAG, 1, 'active')

    try:
        while True:
            # count_data = mag.get_counts()
            # print(f'xs={count_data[0][0]}, xc={count_data[0][1]}')
            # print(f'ys={count_data[1][0]}, yc={count_data[1][1]}')
            #pos_data = mag.get_real_position()
            #print(f'xpos={pos_data[0]}, ypos={pos_data[1]}')
            
            # pid_data = mag.get_data_pid_test()
            # print(f'x_pos={pid_data[0][0]}, y_pos={pid_data[1][0]}')
            # print(f'x_dac={pid_data[0][1]}, y_dac={pid_data[1][1]}')

            # data = mag.get_difcs_msg(counts=True, pos=True, out=True)
            data = mag.get_telemetry()
            print(f'x_sin={data["x_sin"]}, x_cos={data["x_cos"]}')
            print(f'y_sin={data["y_sin"]}, y_cos={data["y_cos"]}')
            print(f'x_pos={data["x_pos"]}')
            print(f'y_pos={data["y_pos"]}')
            print(f'x_out={data["x_out"]}')
            print(f'y_out={data["y_out"]}')

    except KeyboardInterrupt:
        sys.exit("\rclosing")