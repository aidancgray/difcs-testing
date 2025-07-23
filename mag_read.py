import serial
from math import pi, atan, atan2
from serial.serialutil import EIGHTBITS, PARITY_NONE, STOPBITS_ONE


SER_MAG = '/dev/tty.usbmodem586D0017611'
MAX_LIST_LEN = 30

class MagSensor():
    def __init__(self, serial, pole_pitch):
        self.serial = serial            # serial obj
        self.pole_pitch = pole_pitch    # mm
        
        self.n_poles = 0                # int
                                        #   sin, cos, n_poles, x_pos
        self.rdgs = []                  # [(int, int, int,     float)...]
        self.start_p0 = None            #  (int, int, int,     float)
        
        self.start_pos()

    def start_pos(self):
        sin, s_gain, cos, c_gain = self.get_counts()
        # x = (self.pole_pitch/pi)/2 * atan2(-1*float(sin), float(cos))
        self.start_p0 = (sin, s_gain, cos, c_gain)
        self.rdgs.append(self.start_p0)

    def get_sensor_data(self):
        self.serial.reset_input_buffer()
        resp = self.serial.readline()
        msg = resp.decode()

        if msg[0] == "y":
            msg_list = msg.split(',')
            if len(msg_list) != 4:
                return None
            else:
                sin, s_gain, cos, c_gain = msg_list
                sin = sin.split('= ')[1]
                s_gain = s_gain.split('= ')[1]
                cos = cos.split('= ')[1]
                c_gain = c_gain.split('= ')[1]
                return [sin, s_gain, cos, c_gain]
        else:
            return None
    
    def get_counts(self):
        rdout = self.get_sensor_data()
        while not rdout:
            rdout = self.get_sensor_data()
        return int(rdout[0]), int(rdout[1]), int(rdout[2]), int(rdout[3])
    
    # def pole_check(self, sin, cos):
    #     if ( cos < 0 ):
    #         if ( sin > 0 ) and ( self.rdgs[-1][0] < 0):
    #             self.n_poles+=1
    #         elif ( sin < 0 ) and ( self.rdgs[-1][0] > 0):
    #             self.n_poles-=1

    def get_tru_position(self):
        sin, s_gain, cos, c_gain = self.get_counts()
        
        # self.pole_check(sin, cos)
        # x = (self.pole_pitch/pi)/2 * atan2(-1*float(sin), float(cos))
        # x_pos = self.pole_pitch * self.n_poles + x 
        # rdg_n = (sin, cos, self.n_poles, -x_pos)
        
        rdg_n = (sin, s_gain, cos, c_gain)
        self.rdgs.append(rdg_n)
        self.rdgs[-MAX_LIST_LEN:]
        return rdg_n

    def test(self):
        sin, s_gain, cos, c_gain = self.get_counts()
        # x = (self.pole_pitch/pi)/2 * atan2(-1*float(sin), 1*float(cos))
        rdg_n = (sin, s_gain, cos, c_gain)
        return rdg_n

if __name__ == "__main__":
    ser_mag = serial.Serial(port=SER_MAG, 
                            baudrate=128000, 
                            timeout=1, 
                            bytesize=EIGHTBITS,
                            parity=PARITY_NONE,
                            stopbits=STOPBITS_ONE)
    ser_mag.reset_input_buffer()

    mag = MagSensor(ser_mag, 1)

    while True:
        pos = mag.get_tru_position()
        # pos = mag.test()
        print(f'pos={pos}')