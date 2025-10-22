import os
import sys
import time
import serial
import csv
import datetime as dt
from serial.serialutil import SEVENBITS, EIGHTBITS, PARITY_ODD, PARITY_NONE, STOPBITS_ONE


if os.name == "posix":
    DATA_PATH = "/Users/aidancgray/Documents/MIRMOS/DiFCS/testdata/"
    SER_MAG = "/dev/tty.usbserial-B001A17V"
    SER_DIF = "/dev/tty.usbserial-A506NMAT"
    SER_HTR = "/dev/tty.usbserial-14540"
else: 
    DATA_PATH = "C:/Users/Aidan/Documents/MIRMOS/DIFCs_Testing/"
    SER_MAG = 'COM6'
    SER_DIF = 'COM5'
    SER_HTR = 'COM9'

DEBUG = sys.argv[1] if len(sys.argv) > 1 else None

class Lakeshore():
    def __init__(self, port, baudrate, bytesize, parity, stopbits, num_sensors=4, units='K'):
        self.port = port
        self.baudrate= baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.num_sensors = num_sensors
        self.units = units

        self.sensors = {}
        for sns in range(self.num_sensors):
            self.sensors.update({f"t_{sns}": -999})

        self.ser = serial.Serial(port=self.port, 
                                 baudrate=self.baudrate, 
                                 timeout=1, 
                                 bytesize=self.bytesize,
                                 parity=self.parity,
                                 stopbits=self.stopbits)

    def get_temp(self, ser):
        msg = ('CDAT?').encode()
        ser.write(msg)
        resp = ser.readline()
        temp = resp.decode()
    
        temp = temp.split(' ')[0]
        try:
            temp = float(temp)
        except ValueError:
            return -999
        else:
            return temp

if __name__ == "__main__":
    ls = Lakeshore()
    
    try:
        pass
    
    except KeyboardInterrupt:
        print("kb_int")
    finally:
        print("closing")
        sys.exit(0)