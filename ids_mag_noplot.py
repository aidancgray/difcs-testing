import os
import sys
import time
import csv
import serial
import datetime as dt
from serial.serialutil import SEVENBITS, PARITY_ODD, STOPBITS_ONE
from mag_read import MagSensor
import IDSlib.IDS as IDS
from lakeshore import Model336


GET_COUNTS = True
GET_MAG = True
GET_IDS = True
GET_OP = False
GET_TEMPS = True

IDS_IP = "172.16.1.198"
DATA_ACQ_RATE = 100

if os.name == "posix":
    DATA_PATH = "/Users/aidancgray/Documents/MIRMOS/DiFCS/testdata/"
    SER_MAG = "/dev/tty.usbserial-BG01GH9Y"
    SER_HTR = "/dev/tty.usbserial-A506NMAT"
else: 
    DATA_PATH = "C:/Users/Aidan/Documents/MIRMOS/DIFCs_Testing/"
    SER_MAG = 'COM3'
    SER_HTR = 'COM10' 

DEBUG = sys.argv[1] if len(sys.argv) > 1 else None

def dataLoop():
    global data_count

    # Get temp and position data
    temp_htr = get_Lakeshore_temp(ser_htr) if SER_HTR else 0
    temp_a, temp_b, temp_c, temp_d = ls_366.get_all_kelvin_reading()[:4] if GET_TEMPS else (0,0,0,0)

    difcs_data = difcs.get_telemetry()
    if difcs_data:
        mag_x_sin = difcs_data["x_sin"]
        mag_x_cos = difcs_data["x_cos"]
        mag_y_sin = difcs_data["y_sin"]
        mag_y_cos = difcs_data["y_cos"]
        mag_x_pos = difcs_data["x_pos"] 
        mag_y_pos = difcs_data["y_pos"] 

        mag_x_0 = mag_x_pos - start_x_pos
        mag_y_0 = mag_y_pos - start_y_pos

        try:
            (warningNo, pos_1_pm, pos_2_pm, pos_3_pm) = ids.displacement.getAbsolutePositions() if GET_IDS else (None, 0, 0, 0)
            abs_1_um = float(pos_1_pm) / 1000000
            abs_2_um = float(pos_2_pm) / 1000000
            abs_3_um = float(pos_3_pm) / 1000000
            
            ids_x_0 =  -abs_1_um + (float(start_1) /  1000000)
            ids_y_0 =   abs_2_um - (float(start_2) /  1000000)
            ids_z_0 =   abs_3_um - (float(start_3) /  1000000)

            # Add x and y to lists
            meas_time = float("{0:.3f}".format((dt.datetime.now() - start_time).total_seconds()))
            
            data_tmp = [meas_time, 
                        temp_htr,
                        temp_a,
                        temp_b,
                        temp_c,
                        temp_d,
                        mag_x_sin,
                        mag_x_cos,
                        mag_y_sin,
                        mag_y_cos,
                        mag_x_pos,
                        mag_y_pos,
                        abs_1_um,
                        abs_2_um,
                        abs_3_um,
                        mag_x_0,
                        mag_y_0,
                        ids_x_0,
                        ids_y_0,
                        ids_z_0,
                        ]
            if (DEBUG != 'no-write'):
                append_to_csv(dataFile, data_tmp)
            data_count+=1
    
        except ValueError:
            return None

def append_to_csv(dataFile, data):
    with open(f'{dataFile}', 'a', newline='') as fd:
        writer = csv.writer(fd)
        writer.writerow(data)

def get_Lakeshore_temp(ser):
    msg = ('CDAT?\n').encode()
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
    header = ['time',
              'temp_htr', 
              'temp_a', 
              'temp_b', 
              'temp_c', 
              'temp_d', 
              'x_sin', 
              'x_cos', 
              'y_sin', 
              'y_cos', 
              'x_pos', 
              'y_pos', 
              'ids_x', 
              'ids_y',
              'ids_z',
              'mag_x_0',
              'mag_y_0',
              'ids_x_0',
              'ids_y_0',
              'ids_z_0',
              ]
    
    if SER_HTR:
        ser_htr = serial.Serial(port=SER_HTR, 
                                baudrate=1200, 
                                timeout=1, 
                                bytesize=SEVENBITS,
                                parity=PARITY_ODD,
                                stopbits=STOPBITS_ONE)
    
    ls_366 = Model336()

    if GET_IDS:
        ids = IDS.Device(IDS_IP) 
        ids.connect()
        
        if not ids.displacement.getMeasurementEnabled():
            ids.system.setInitMode(0) # enable high accuracy mode
            ids.system.startMeasurement()
            while not ids.displacement.getMeasurementEnabled():
                time.sleep(1)
    
    difcs = MagSensor(SER_MAG, 1, 'active') if (GET_COUNTS or GET_MAG) else None

    print(f'dataFile: {dataFile}')
    append_to_csv(dataFile, header)


    # Get starting values
    start_time = dt.datetime.now()
    
    start_t_htr = get_Lakeshore_temp(ser_htr) if SER_HTR else 0
    start_t_a, start_t_b, start_t_c, start_t_d = ls_366.get_all_kelvin_reading()[:4]
    
    (warningNo, start_1, start_2, start_3) = ids.displacement.getAbsolutePositions() if GET_IDS else (None, 0, 0, 0)

    print(difcs.get_telemetry())
    print(difcs.get_telemetry())
    print(difcs.get_telemetry())
    difcs_msg = difcs.get_telemetry()
    print(difcs_msg)
    start_x_pos = difcs_msg["x_pos"]
    start_y_pos = difcs_msg["y_pos"]
    
    data_count = 0
    time_start = time.perf_counter()
    try:
        while True:
            dataLoop()
            time.sleep(DATA_ACQ_RATE/1000)
    except KeyboardInterrupt:
        print("kb_int")
    finally:
        time_stop = time.perf_counter()
        print(f"{data_count} / {'{0:.2f}'.format(time_stop-time_start)}")
        print("closing")
        sys.exit(0)