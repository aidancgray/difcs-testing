import sys
import time
import csv
import serial
import datetime as dt
from math import floor
from serial.serialutil import SEVENBITS, EIGHTBITS, PARITY_ODD, PARITY_NONE, STOPBITS_ONE
from mag_read import MagSensor
import IDS


DATA_PATH = "/Users/aidancgray/Documents/MIRMOS/DiFCS/mag-sensor/"
IDS_IP = "172.16.1.198"
ANIM_INTER = 500
DATA_LIMIT = 30
SER_DIF = '/dev/tty.usbserial-A506NMAT'
SER_MAG = '/dev/tty.usbmodem586D0017611'

DEBUG = sys.argv[1] if len(sys.argv) > 1 else None

# This function is called periodically from FuncAnimation
def get_data():
    # Get temp and position data
    temp_dif = start_t
    rdng = mag.get_tru_position()
    mag_sin = rdng[0]
    mag_sin_gain = rdng[1]
    mag_cos = rdng[2]
    mag_cos_gain = rdng[3]

    try:
        warningNo, pos_1_pm, pos_2_pm, pos_3_pm = ids.displacement.getAbsolutePositions()
        abs_2_um = float(pos_2_pm) / 1000000
        pos_2_um = float(pos_2_pm - start_2) / 1000000

        # Add x and y to lists
        meas_time = float("{0:.3f}".format((dt.datetime.now() - start_time).total_seconds()))
        
        data = [meas_time, 
                temp_dif if temp_dif else '--', 
                mag_sin,
                mag_sin_gain,
                mag_cos,
                mag_cos_gain,
                abs_2_um,
                pos_2_um,]

    except ValueError:
        return None
    else:
        return data
    
def print_data(data):
    sin = data[2]
    s_gain = data[3]
    cos = data[4]
    c_gain = data[5]
    ids = data[7]

    print(f'| {sin:> 6.0f}({s_gain:>2}x) {cos:> 6.0f}({c_gain:>2}x) | {ids:> 9.3f}')

def append_to_csv(dataFile, data):
    with open(f'{dataFile}', 'a') as fd:
        writer = csv.writer(fd)
        writer.writerow(data)

def get_Lakeshore_temp(ser):
    msg = ('CDAT?').encode()
    ser.write(msg)
    resp = ser.readline()
    ls_temp = resp.decode()

    ls_temp = ls_temp.split(' ')[0]
    try:
        ls_temp = float(ls_temp)
    except ValueError:
        return -999
    else:
        return ls_temp

if __name__ == "__main__":
    dataFile = f"{DATA_PATH}{dt.datetime.now().strftime('%d%m%Y_%H-%M-%S')}.csv"
    header = ['time', 'temp', 'mag_sin', 'mag_sin_gain', 'mag_cos', 'mag_cos_gain', 'ids', 'ids_off']
    ser_mag = serial.Serial(port=SER_MAG, 
                            baudrate=128000, 
                            timeout=1, 
                            bytesize=EIGHTBITS,
                            parity=PARITY_NONE,
                            stopbits=STOPBITS_ONE)

    ser_dif = serial.Serial(port=SER_DIF, 
                            baudrate=1200, 
                            timeout=1, 
                            bytesize=SEVENBITS,
                            parity=PARITY_ODD,
                            stopbits=STOPBITS_ONE)

    ids = IDS.Device(IDS_IP)
    ids.connect()
    
    if not ids.displacement.getMeasurementEnabled():
        ids.system.setInitMode(0) # enable high accuracy mode
        ids.system.startMeasurement()
        while not ids.displacement.getMeasurementEnabled():
            time.sleep(1)
    
    ser_mag.reset_input_buffer()
    mag = MagSensor(ser_mag, 1)

    print(f'dataFile: {dataFile}')
    append_to_csv(dataFile, header)

    mode = input('enter \'S\' for single-point manual mode OR any other key for rapid automatic mode:')
    print(f'running in {"MANUAL" if mode.upper() == "S" else "AUTO"} mode...')
    begin_wait = input('press ENTER to begin data collection')

    # Get starting values
    start_time = dt.datetime.now()
    # start_mag_pos = mag.get_tru_position()[-1]
    start_t = get_Lakeshore_temp(ser_dif) if SER_DIF else None
    warningNo, start_1, start_2, start_3 = ids.displacement.getAbsolutePositions()
    
    try:
        while True:
            dat_start_time = dt.datetime.now()
            data = get_data()
            dat_time = f'{(dt.datetime.now()-dat_start_time).total_seconds():0.3f}'
            append_to_csv(dataFile, data)
            data.append(dat_time)
            print_data(data)
            # time.sleep(0.001)
            loop = input() if mode.upper() == 'S' else None
    except KeyboardInterrupt:
        print("exiting...")
        print(f'dataFile: {dataFile}')

        sys.exit()