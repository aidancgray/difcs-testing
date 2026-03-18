import serial
from serial.serialutil import EIGHTBITS, PARITY_NONE, STOPBITS_ONE

class ReadLine:
    def __init__(self, s):
        self.buf = bytearray()
        self.s = s
    
    def readline(self):
        i = self.buf.find(b"\n")
        if i >= 0:
            r = self.buf[:i+1]
            self.buf = self.buf[i+1:]
            return r
        while True:
            i = max(1, min(2048, self.s.in_waiting))
            data = self.s.read(i)
            i = data.find(b"\n")
            if i >= 0:
                r = self.buf + data[:i+1]
                self.buf[0:] = data[i+1:]
                return r
            else:
                self.buf.extend(data)

ser = serial.Serial(port='COM3', 
                    baudrate=128000, 
                    timeout=1, 
                    bytesize=EIGHTBITS,
                    parity=PARITY_NONE,
                    stopbits=STOPBITS_ONE)
rl = ReadLine(ser)
msg = '~D0,gTlm\n'
while True:
    ser.write(msg.encode('utf-8'))
    print(rl.readline())