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


RADIUS = 50   # um
D_RADIUS = 1  # um
SPEED = 2.5   # deg/min


SETPOINT_LIST = []

SP_MAX   =  200
SP_MIN   = -200
SP_STEP  =   10
SP_TIMER =   29

LOOPS = 4

FLIP_CHANNELS = True
GET_COUNTS = True
GET_MAG = True
GET_IDS = True
GET_OP = True
GET_TEMPS = False

IDS_IP = "172.16.1.198"
DATA_RATE = 400

if os.name == "posix":
    DATA_PATH = "/Users/aidancgray/Documents/MIRMOS/DiFCS/testdata/"
    SER_MAG = "/dev/tty.usbserial-BG01GH9Y"
    SER_HTR = "/dev/tty.usbserial-A506NMAT"
else: 
    DATA_PATH = "C:/Users/Aidan/Documents/MIRMOS/DIFCs_Testing/"
    SER_MAG = 'COM3'
    SER_HTR = 'COM10'

if len(sys.argv) < 2:
    CHANNEL = 1
else:
    CHANNEL = int(sys.argv[1])

DEBUG = sys.argv[2] if len(sys.argv) > 2 else None


def setpoint_increment(channel):
    global sp_incr
    global loop
    if sp_incr >= len(SETPOINT_LIST):
        loop+=1
        print(f"--- LOOP {loop} START ---")
        sp_incr = 0
    new_sp_offset = SETPOINT_LIST[sp_incr]    
    new_sp = new_sp_offset + [start_x_pos, start_y_pos][chn-1]
    difcs.set_sp(channel, new_sp)
    sp_incr+=1
    return new_sp_offset

def setpoint_timer(channel):
    global sp_timer
    if sp_timer == SP_TIMER:
        sp_timer = 0
        new_sp = setpoint_increment(channel)
        return new_sp
    else:
        sp_timer+=1
        return None

def dataLoop():
    global chn
    global setpoint
    global data_count

    # Get temp and position data
    temp_htr = get_Lakeshore_temp(ser_htr) if (SER_HTR and GET_TEMPS) else 0  # noqa: F841
    temp_a, temp_b, temp_c, temp_d = ls_366.get_all_kelvin_reading()[:4] if GET_TEMPS else (0,0,0,0)

    dac_x = 0
    dac_y = 0
    
    difcs_data = difcs.get_telemetry()
    if difcs_data:
        mag_x_sin = difcs_data["x_sin"]
        mag_x_cos = difcs_data["x_cos"]
        mag_y_sin = difcs_data["y_sin"]
        mag_y_cos = difcs_data["y_cos"]
        mag_x_pos = difcs_data["x_pos"]
        mag_y_pos = difcs_data["y_pos"]
        dac_x     = difcs_data["x_out"]
        dac_y     = difcs_data["y_out"]

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
                        setpoint,
                        dac_x,
                        dac_y, 
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
        
        sp_ret = setpoint_timer(chn)
        if sp_ret is not None:
            print(f"   {chn}: {sp_ret}um")
            setpoint = sp_ret
        
        return data_count

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
    chn = CHANNEL
    sp_incr = 0
    sp_timer = 0
    setpoint = 0
    loop = 0

    dataFile = f"{DATA_PATH}{dt.datetime.now().strftime('%d%m%Y_%H-%M-%S')}_pid_{chn}_{DEBUG}.csv"
    if FLIP_CHANNELS:
        header = ['time',
                  'setpoint', 
                  'dac_y', 
                  'dac_x', 
                  'y_sin', 
                  'y_cos', 
                  'x_sin', 
                  'x_cos', 
                  'y_pos', 
                  'x_pos', 
                  'ids_x', 
                  'ids_y',
                  'ids_z',
                  'mag_y_0',
                  'mag_x_0',
                  'ids_x_0',
                  'ids_y_0',
                  'ids_z_0',]
    else:
        header = ['time',
                  'setpoint', 
                  'dac_x', 
                  'dac_y', 
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
                  'ids_z_0',]
    
    if (SER_HTR and GET_TEMPS):
        ser_htr = serial.Serial(port=SER_HTR, 
                                baudrate=1200, 
                                timeout=1, 
                                bytesize=SEVENBITS,
                                parity=PARITY_ODD,
                                stopbits=STOPBITS_ONE)
    else:
        ser_htr = None
    
    ls_366 = Model336() if GET_TEMPS else None

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
    if input("(S)tart | (Q)uit: ").upper == "Q":
        print("closing...")
        sys.exit(0)
    else:
        print("starting...")
    
    # Get starting values
    start_time = dt.datetime.now()
    
    start_t_htr = get_Lakeshore_temp(ser_htr) if ser_htr else 0
    start_t_a, start_t_b, start_t_c, start_t_d = ls_366.get_all_kelvin_reading()[:4] if ls_366 else 0,0,0,0
    
    (warningNo, start_1, start_2, start_3) = ids.displacement.getAbsolutePositions() if GET_IDS else (None, 0, 0, 0)
    
    print(difcs.get_telemetry())
    print(difcs.get_telemetry())
    print(difcs.get_telemetry())
    difcs_msg = difcs.get_telemetry()
    print(difcs_msg)
    start_x_pos = difcs_msg["x_pos"]
    start_y_pos = difcs_msg["y_pos"]
    
    init_sp = [start_x_pos, start_y_pos][chn-1]
    print(f"start position setpoint:{init_sp}")
    difcs.set_sp(chn, init_sp)
    difcs.set_ChMode(chn, 'MAGSNS')

    data_count = 0
    time_start = time.perf_counter()
    try:
        while loop < LOOPS:
            resp = dataLoop()
            time.sleep(DATA_RATE/1000)
    except KeyboardInterrupt:
        print("kb_int")
    finally:
        time_stop = time.perf_counter()
        print(f'{data_count} / {"{0:.2f}".format(time_stop-time_start)}')
        difcs.set_ChMode(1,'MANUAL')
        difcs.set_ChMode(2,'MANUAL')
        print("closing")
        sys.exit(0)