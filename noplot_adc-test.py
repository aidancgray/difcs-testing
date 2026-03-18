import os
import sys
import time
import csv
import datetime as dt
from mag_read import MagSensor


FLIP_CHANNELS = True
DATA_ACQ_RATE = 1000

if os.name == "posix":
    DATA_PATH = "/Users/aidancgray/Documents/MIRMOS/DiFCS/testdata/"
    SER_MAG = "/dev/tty.usbserial-BG01GH9Y"
else: 
    DATA_PATH = "C:/Users/Aidan/Documents/MIRMOS/DIFCs_Testing/"
    SER_MAG = 'COM3'

DEBUG = sys.argv[1] if len(sys.argv) > 1 else None

def dataLoop():
    global data_count

    difcs_data = difcs.get_counts_adctest()
    if difcs_data:
        ch_0_sin = difcs_data["ch_0_sin"]
        ch_0_cos = difcs_data["ch_0_cos"]
        ch_1_sin = difcs_data["ch_1_sin"]
        ch_1_cos = difcs_data["ch_1_cos"]

        try:
            # Add x and y to lists
            meas_time = float("{0:.3f}".format((dt.datetime.now() - start_time).total_seconds()))
            
            data_tmp = [meas_time, 
                        ch_0_sin,
                        ch_0_cos,
                        ch_1_sin,
                        ch_1_cos,
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

if __name__ == "__main__":
    dataFile = f"{DATA_PATH}{dt.datetime.now().strftime('%d%m%Y_%H-%M-%S')}_adc-test_{DEBUG}.csv"
    header = ['time',
              'ch_0_sin', 
              'ch_0_cos', 
              'ch_1_sin', 
              'ch_1_cos',]

    difcs = MagSensor(SER_MAG, 1, 'passive')

    print(f'dataFile: {dataFile}')
    append_to_csv(dataFile, header)

    # Get starting values
    start_time = dt.datetime.now()
        
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