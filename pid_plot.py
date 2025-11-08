# data lists: 
# time, 
# x_sin, x_cos, y_sin, y_cos, 
# x_pos, y_pos, 
# ids_x, ids_y, ids_z
# t_dif, t_htr 

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


IDS_IP = "172.16.1.198"
DIFCS_IP = "172.16.2.61"
DIFCS_PORT = 8234
ANIM_INTER = 50
DATA_LIMIT = 300
NO_COUNTS = True

if os.name == "posix":
    DATA_PATH = "/Users/aidancgray/Documents/MIRMOS/DiFCS/testdata/"
    SER_MAG = "/dev/tty.usbserial-B001A17V"
    SER_DIF = None 
    SER_HTR = "/dev/tty.usbserial-A506NMAT"
else: 
    DATA_PATH = "C:/Users/Aidan/Documents/MIRMOS/DIFCs_Testing/"
    SER_MAG = 'COM6'
    SER_DIF = None #'COM5'
    SER_HTR = None #'COM10'

# DEBUG = sys.argv[1] if len(sys.argv) > 1 else None
DEBUG = None

if len(sys.argv) != 2:
    sys.exit('NO CHANNEL SPECIFIED')

CHANNEL = int(sys.argv[1])
SETPOINT_LIST = [ 0, 5, 10, 20, 40, 60, 40, 20, 10, 5, 0, 1, 2, 3, 2, 1, 0]
SETPOINT_TIMER = 50

def setpoint_increment(channel):
    global sp_incr
    if sp_incr >= len(SETPOINT_LIST):
        sp_incr = 0
    new_sp = SETPOINT_LIST[sp_incr] + start_pos_data[channel-1]
    mag.set_sp(channel, new_sp)
    sp_incr+=1
    return new_sp

def setpoint_timer(channel):
    global sp_timer
    if sp_timer == SETPOINT_TIMER:
        sp_timer = 0
        new_sp = setpoint_increment(channel)
        return new_sp
    else:
        sp_timer+=1
        return None

# This function is called periodically from FuncAnimation
def animate(i, t, x_sin, x_cos, y_sin, y_cos, x_pos, y_pos, ids_x, ids_y, ids_z):
    global chn
    global setpoint

    # Get temp and position data
    temp_dif = get_Lakeshore_temp(ser_dif) if SER_DIF else None
    temp_htr = get_Lakeshore_temp(ser_htr) if SER_HTR else None

    cv = 0 #mag.get_CV(chn)

    # counts_data = mag.get_counts()
    counts_data = ((0,0),(0,0))
    mag_x_sin = counts_data[0][0]
    mag_x_cos = counts_data[0][1]
    mag_y_sin = counts_data[1][0]
    mag_y_cos = counts_data[1][1]

    pos_data = mag.get_real_position()
    mag_x_pos = pos_data[0] - start_x_pos
    mag_y_pos = pos_data[1] - start_y_pos
    
    try:
        warningNo, pos_1_pm, pos_2_pm, pos_3_pm = ids.displacement.getAbsolutePositions()

        pos_1_um = float(pos_1_pm - start_1) / -1000000
        pos_2_um = float(pos_2_pm - start_2) /  1000000
        pos_3_um = float(pos_3_pm - start_3) /  1000000

        # Add x and y to lists
        meas_time = float("{0:.3f}".format((dt.datetime.now() - start_time).total_seconds()))
        
        data_tmp = [meas_time,
                    setpoint,
                    cv, 
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

    else:
        fig.clear()  # clear
        ax1, ax2 = setup_plots()

        # Draw x and y lists
        marker_fmt = '.'
        ms_fmt = 5
        lw_fmt = 1

        # l_xs, = ax1.plot(t, x_sin, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='red')
        # l_xc, = ax1.plot(t, x_cos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='blue')

        # l_ys, = ax2.plot(t, y_sin, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='red')
        # l_yc, = ax2.plot(t, y_cos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='blue')
        
        l_xp, = ax1.plot(t, x_pos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='red')
        l_ids_x, = ax2.plot(t, ids_x, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='red')
        l_yp, = ax1.plot(t, y_pos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='blue')
        l_ids_y, = ax2.plot(t, ids_y, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='blue')

        xy_pos_0 = (1.01, 0.95)
        xy_pos_1 = (1.01, 0.70)
        xy_pos_2 = (1.01, 0.45)
        xy_pos_3 = (1.01, 0.20)
        
        ax1.annotate(f'x_pos: {mag_x_pos}', xy=xy_pos_0, xycoords='axes fraction',
                     size=10, ha='left', va='top', 
                     bbox=dict(boxstyle='round', fc='w'))
        ax1.annotate(f'y_pos: {mag_y_pos}', xy=xy_pos_1, xycoords='axes fraction',
                     size=10, ha='left', va='top', 
                     bbox=dict(boxstyle='round', fc='w'))
        ax1.annotate(f'sp: {setpoint}', xy=xy_pos_2, xycoords='axes fraction',
                     size=10, ha='left', va='top', 
                     bbox=dict(boxstyle='round', fc='w'))
        ax1.annotate(f'cv: {cv}%', xy=xy_pos_3, xycoords='axes fraction',
                     size=10, ha='left', va='top', 
                     bbox=dict(boxstyle='round', fc='w'))
        
        ax2.annotate(f'x_ids: {pos_1_um}', xy=xy_pos_0, xycoords='axes fraction',
                     size=10, ha='left', va='top', 
                     bbox=dict(boxstyle='round', fc='w'))
        ax2.annotate(f'y_ids: {pos_2_um}', xy=xy_pos_1, xycoords='axes fraction',
                     size=10, ha='left', va='top', 
                     bbox=dict(boxstyle='round', fc='w'))
        
        plt.draw()
        append_to_csv(dataFile, data_tmp)

        sp_ret = setpoint_timer(chn)
        if sp_ret != None:
            print(f"   {chn}: {sp_ret}um")
            setpoint = sp_ret

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
    sp_incr = 0
    sp_timer = 0
    setpoint = 0

    dataFile = f"{DATA_PATH}{dt.datetime.now().strftime('%d%m%Y_%H-%M-%S')}.csv"
    header = ['time',
              'setpoint',
              'cv', 
              'x_sin', 
              'x_cos', 
              'y_sin', 
              'y_cos', 
              'x_pos', 
              'y_pos', 
              'ids_x', 
              'ids_y',
              'ids_z',]
    
    if SER_DIF:
        ser_dif = serial.Serial(port=SER_DIF, 
                                baudrate=1200, 
                                timeout=1, 
                                bytesize=SEVENBITS,
                                parity=PARITY_ODD,
                                stopbits=STOPBITS_ONE)
    
    if SER_HTR:
        ser_htr = serial.Serial(port=SER_HTR, 
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
    
    mag = MagSensor(SER_MAG, 1, 'passive')

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

    l_xp, = ax1.plot(t, x_pos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='red')
    l_ids_x, = ax2.plot(t, ids_x, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='red')
    l_yp, = ax1.plot(t, y_pos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='blue')
    l_ids_y, = ax2.plot(t, ids_y, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='blue')

    # Get starting values
    start_time = dt.datetime.now()
    
    start_t_htr = get_Lakeshore_temp(ser_htr) if SER_DIF else None
    
    warningNo, start_1, start_2, start_3 = ids.displacement.getAbsolutePositions()
    start_pos_data = mag.get_real_position()
    start_x_pos = start_pos_data[0]
    start_y_pos = start_pos_data[1]
    setpoint = start_pos_data[chn-1]
    print(f"start position setpoint:{setpoint}")
    mag.set_sp(chn, setpoint)
    mag.set_ChMode(chn, 'MAGSNS')

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
        # mag.dis_PID(1)
        # mag.dis_PID(2)
        mag.set_ChMode(1,'MANUAL')
        mag.set_ChMode(2,'MANUAL')
        print("closing")
        sys.exit(0)