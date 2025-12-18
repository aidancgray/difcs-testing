import os
import sys
import time
import csv
import serial
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from serial.serialutil import SEVENBITS, EIGHTBITS, PARITY_ODD, PARITY_NONE, STOPBITS_ONE
from mag_read import MagSensor
import IDSlib.IDS as IDS
from lakeshore import Model336


GET_COUNTS = True
GET_MAG = True
GET_IDS = True
GET_OP = False
GET_TEMPS = True

IDS_IP = "172.16.1.198"
ANIM_INTER = 100
DATA_LIMIT = 100

if os.name == "posix":
    DATA_PATH = "/Users/aidancgray/Documents/MIRMOS/DiFCS/testdata/"
    SER_MAG = "/dev/tty.usbserial-BG01GH9Y"
    SER_HTR = None #"/dev/tty.usbserial-A506NMAT"
else: 
    DATA_PATH = "C:/Users/Aidan/Documents/MIRMOS/DIFCs_Testing/"
    SER_MAG = 'COM3'
    SER_HTR = 'COM10'
    # SER_HTR = None

DEBUG = sys.argv[1] if len(sys.argv) > 1 else None

# OUTPUT_LIST = [  5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95,100,
#                 95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10,  5,  0,
                # -5,-10,-15,-10, -5,  0]

OUTPUT_LIST = [  5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75,
                70, 65, 60, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10,  5,  0, 
                -5,-10,-15,-10, -5,  0]

# OUTPUT_LIST = [  5, 10, 15, 10,  5,  0 ]
CHANNEL = sys.argv[1]
OUTPUT_TIMER = 30

def output_increment(channel):
    global op_incr
    
    if op_incr >= len(OUTPUT_LIST):
        op_incr = 0
    
    new_op = OUTPUT_LIST[op_incr]
    difcs.set_op(new_op, channel)
    op_incr+=1
    return new_op

def output_timer(channel):
    global op_timer
    if op_timer == OUTPUT_TIMER:
        op_timer = 0
        new_op = output_increment(channel)
        return new_op
    else:
        op_timer+=1
        return None

# This function is called periodically from FuncAnimation
def animate(i, t, x_sin, x_cos, y_sin, y_cos, x_pos, y_pos, ids_x, ids_y, ids_z):
    global chn
    global op_percent
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
        mag_x_pos = difcs_data["x_pos"] - start_x_pos
        mag_y_pos = difcs_data["y_pos"] - start_y_pos
    
        try:
            (warningNo, pos_1_pm, pos_2_pm, pos_3_pm) = ids.displacement.getAbsolutePositions() if GET_IDS else (None,0,0,0)
            pos_1_um = float(pos_1_pm - start_1) / -1000000
            pos_2_um = float(pos_2_pm - start_2) /  1000000
            pos_3_um = float(pos_3_pm - start_3) /  1000000

            # Add x and y to lists
            meas_time = float("{0:.3f}".format((dt.datetime.now() - start_time).total_seconds()))
            
            data_tmp = [meas_time,
                        op_percent, 
                        mag_x_sin,
                        mag_x_cos,
                        mag_y_sin,
                        mag_y_cos,
                        mag_x_pos,
                        mag_y_pos,
                        pos_1_um,
                        pos_2_um,
                        pos_3_um,
                        ]
            if (DEBUG != 'no-write'):
                append_to_csv(dataFile, data_tmp)
            data_count+=1
            
            t.append(meas_time)

            x_sin.append(mag_x_sin)
            x_cos.append(mag_x_cos)
            x_pos.append(mag_x_pos)
            
            y_sin.append(mag_y_sin)
            y_cos.append(mag_y_cos)
            y_pos.append(mag_y_pos)

            ids_x.append(pos_1_um)
            ids_y.append(pos_2_um)
            ids_z.append(pos_3_um)

            # Limit x and y lists to DATA_LIMIT items
            t = t[-DATA_LIMIT:]
            x_sin = x_sin[-DATA_LIMIT:]
            x_cos = x_cos[-DATA_LIMIT:]
            x_pos = x_pos[-DATA_LIMIT:]
            
            y_sin = y_sin[-DATA_LIMIT:]
            y_cos = y_cos[-DATA_LIMIT:]
            y_pos = y_pos[-DATA_LIMIT:]

            ids_x = ids_x[-DATA_LIMIT:]
            ids_y = ids_y[-DATA_LIMIT:]
            ids_z = ids_z[-DATA_LIMIT:]
        
        except ValueError:
            return None

    
    fig.clear()
    ax1, ax2 = setup_plots()

    # Draw x and y lists
    marker_fmt = '.'
    ms_fmt = 5
    lw_fmt = 1
    
    l_xp,    = ax1.plot(t, x_pos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='red')
    l_ids_x, = ax2.plot(t, ids_x, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='orange')
    l_yp,    = ax1.plot(t, y_pos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='blue')
    l_ids_y, = ax2.plot(t, ids_y, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='green')

    xy_pos_0 = (1.01, 0.95)
    xy_pos_1 = (1.01, 0.70)
    xy_pos_2 = (1.01, 0.45)
    
    ax1.annotate(f'x_pos: {"{0:.3f}".format(x_pos[-1])}', xy=xy_pos_0, xycoords='axes fraction',
                    size=10, ha='left', va='top', color='red',
                    bbox=dict(boxstyle='round', fc='w'))
    ax1.annotate(f'y_pos: {"{0:.3f}".format(y_pos[-1])}', xy=xy_pos_1, xycoords='axes fraction',
                    size=10, ha='left', va='top', color='blue', 
                    bbox=dict(boxstyle='round', fc='w'))
    ax1.annotate(f'op: {"{0:.2f}".format(op_percent)}%', xy=xy_pos_2, xycoords='axes fraction',
                    size=10, ha='left', va='top', 
                    bbox=dict(boxstyle='round', fc='w'))
    
    ax2.annotate(f'x_ids: {"{0:.3f}".format(ids_x[-1])}', xy=xy_pos_0, xycoords='axes fraction',
                    size=10, ha='left', va='top', color='orange', 
                    bbox=dict(boxstyle='round', fc='w'))
    ax2.annotate(f'y_ids: {"{0:.3f}".format(ids_y[-1])}', xy=xy_pos_1, xycoords='axes fraction',
                    size=10, ha='left', va='top', color='green', 
                    bbox=dict(boxstyle='round', fc='w'))
    
    plt.draw()

    op_ret = output_timer(chn)

    if op_ret != None:
        print(f"   {chn}: {op_ret}%")
        op_percent = op_ret

    return l_xp, l_yp, l_ids_x, l_ids_y

def setup_plots():
    gs = fig.add_gridspec(2, 1, wspace=0, hspace=0.1)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, 0])

    ax1.grid()
    ax2.grid()

    ax1.set_ylabel(r'pos')
    ax1.tick_params(labelbottom=False)
    
    ax2.set_xlabel('Elapsed Time (s)')
    ax2.set_ylabel(r'pos')
    ax2.tick_params(axis='x', labelrotation=45)
    
    return ax1, ax2

def append_to_csv(dataFile, data):
    with open(f'{dataFile}', 'a', newline='') as fd:
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
    chn = CHANNEL
    op_incr = 0
    op_timer = 0
    op_percent = 0

    dataFile = f"{DATA_PATH}{dt.datetime.now().strftime('%d%m%Y_%H-%M-%S')}_{chn}.csv"
    header = ['time',
              'output', 
              'x_sin', 
              'x_cos', 
              'y_sin', 
              'y_cos', 
              'x_pos', 
              'y_pos', 
              'ids_x', 
              'ids_y',
              'ids_z',]
    
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

    # Create figure for plotting
    fig = plt.figure()
    ax1, ax2 = setup_plots()

    t = [] 
    x_sin, x_cos, x_pos = [], [], []
    y_sin, y_cos, y_pos = [], [], []
    ids_x, ids_y, ids_z = [], [], []

    # Draw x and y lists
    marker_fmt = '.'
    ms_fmt = 10
    lw_fmt = 1

    l_xp,    = ax1.plot(t, x_pos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='red')
    l_ids_x, = ax2.plot(t, ids_x, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='orange')
    l_yp,    = ax1.plot(t, y_pos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='blue')
    l_ids_y, = ax2.plot(t, ids_y, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='green')

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
        # Set up plot to call animate() function periodically
        ani = animation.FuncAnimation(fig, 
                                    animate, 
                                    fargs=(t, x_sin, x_cos, y_sin, y_cos, x_pos, y_pos, ids_x, ids_y, ids_z), 
                                    interval=ANIM_INTER,
                                    cache_frame_data=False)
        
        manager = plt.get_current_fig_manager()
        if os.name == "posix":
            manager.full_screen_toggle()
        else:    
            manager.resize(1280, 720)
        plt.show()
        plt.pause(.01)
    except KeyboardInterrupt:
        print("kb_int")
    finally:
        time_stop = time.perf_counter()
        print(f"{data_count} / {"{0:.2f}".format(time_stop-time_start)}")
        difcs.set_op(0, 1)
        difcs.set_op(0, 2)
        print("closing")
        sys.exit(0)