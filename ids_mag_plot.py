import os
import sys
import time
import csv
import serial
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from serial.serialutil import SEVENBITS, PARITY_ODD, STOPBITS_ONE
from mag_read import MagSensor
import IDSlib.IDS as IDS
from lakeshore import Model336


GET_COUNTS = True
GET_MAG = True
GET_IDS = True

IDS_IP = "172.16.1.198"
DIFCS_IP = "172.16.2.61"
DIFCS_PORT = 8234
ANIM_INTER = 500
DATA_LIMIT = 100

if os.name == "posix":
    DATA_PATH = "/Users/aidancgray/Documents/MIRMOS/DiFCS/testdata/"
    SER_MAG = "/dev/tty.usbserial-B001A17V"
    SER_DIF = None
    SER_HTR = "/dev/tty.usbserial-A506NMAT"
else: 
    DATA_PATH = "C:/Users/Aidan/Documents/MIRMOS/DIFCs_Testing/"
    SER_MAG = 'COM3'
    # SER_DIF = 'COM5'
    SER_HTR = 'COM10'

DEBUG = sys.argv[1] if len(sys.argv) > 1 else None

# This function is called periodically from FuncAnimation
def animate(i, t, t_htr, t_a, t_b, t_c, t_d, x_sin, x_cos, y_sin, y_cos, x_pos, y_pos, ids_x, ids_y, ids_z):
    # Get temp and position data
    temp_htr = get_Lakeshore_temp(ser_htr) if SER_HTR else None
    temp_a, temp_b, temp_c, temp_d = ls_366.get_all_kelvin_reading()[:4]

    # counts_data = mag.get_counts() if GET_COUNTS else ((0,0),(0,0))
    # mag_x_sin = counts_data[0][0] 
    # mag_x_cos = counts_data[0][1] 
    # mag_y_sin = counts_data[1][0] 
    # mag_y_cos = counts_data[1][1] 

    # pos_data = mag.get_real_position() if GET_MAG else (0,0)
    # mag_x_pos = pos_data[0] - start_x_pos
    # mag_y_pos = pos_data[1] - start_y_pos

    difcs_data = mag.get_difcs_msg(counts=GET_COUNTS, pos=GET_MAG)
    mag_x_sin = difcs_data["x_sin"]
    mag_x_cos = difcs_data["x_cos"]
    mag_y_sin = difcs_data["y_sin"]
    mag_y_cos = difcs_data["y_cos"]
    mag_x_pos = difcs_data["x_pos"] - start_x_pos
    mag_y_pos = difcs_data["y_pos"] - start_y_pos

    try:
        (warningNo, pos_1_pm, pos_2_pm, pos_3_pm) = ids.displacement.getAbsolutePositions() if GET_IDS else (None, 0, 0, 0)
        pos_1_um = float(pos_1_pm - start_1) / 1000000
        pos_2_um = float(pos_2_pm - start_2) / 1000000
        pos_3_um = float(pos_3_pm - start_3) / 1000000

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
                    pos_1_um,
                    pos_2_um,
                    pos_3_um,
                    ]

        t.append(meas_time)

        t_htr.append(temp_htr)
        t_a.append(temp_a)
        t_b.append(temp_b)
        t_c.append(temp_c)
        t_d.append(temp_d)

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

        t_htr = t_htr[-DATA_LIMIT:]
        t_a = t_a[-DATA_LIMIT:]
        t_b = t_b[-DATA_LIMIT:]
        t_c = t_c[-DATA_LIMIT:]
        t_d = t_d[-DATA_LIMIT:]
        
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
        fig.clear()
        # ax1, ax2 = setup_plots()
        ax1 = setup_plots()

        # Draw x and y lists
        marker_fmt = '.'
        ms_fmt = 5
        lw_fmt = 1

        # l_t_htr, = ax2.plot(t, t_htr, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='blue')
        # l_t_a,   = ax2.plot(t, t_a, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='green')
        # l_t_b,   = ax2.plot(t, t_b, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='orange')
        # l_t_c,   = ax2.plot(t, t_c, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='red')
        # l_t_d,   = ax2.plot(t, t_d, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='purple')

        l_xp,    = ax1.plot(t, x_pos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='red')
        l_ids_x, = ax1.plot(t, ids_x, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='orange')
        l_yp,    = ax1.plot(t, y_pos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='blue')
        l_ids_y, = ax1.plot(t, ids_y, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='green')

        xy_pos_0 = (1.01, 0.95)
        xy_pos_1 = (1.01, 0.70)
        xy_pos_2 = (1.01, 0.45)
        xy_pos_3 = (1.01, 0.20)
        xy_pos_4 = (1.01, -0.05)
        
        ax1.annotate(f'x_pos: {"{0:.3f}".format(mag_x_pos)}', xy=xy_pos_0, xycoords='axes fraction',
                     size=10, ha='left', va='top', color='red',
                     bbox=dict(boxstyle='round', fc='w'))
        ax1.annotate(f'y_pos: {"{0:.3f}".format(mag_y_pos)}', xy=xy_pos_2, xycoords='axes fraction',
                     size=10, ha='left', va='top', color='blue', 
                     bbox=dict(boxstyle='round', fc='w'))
        
        ax1.annotate(f'x_ids: {"{0:.3f}".format(pos_1_um)}', xy=xy_pos_1, xycoords='axes fraction',
                     size=10, ha='left', va='top', color='orange', 
                     bbox=dict(boxstyle='round', fc='w'))
        ax1.annotate(f'y_ids: {"{0:.3f}".format(pos_2_um)}', xy=xy_pos_3, xycoords='axes fraction',
                     size=10, ha='left', va='top', color='green', 
                     bbox=dict(boxstyle='round', fc='w'))
        
        # ax2.annotate(f't_htr: {temp_htr} K', xy=xy_pos_0, xycoords='axes fraction',
        #              size=10, ha='left', va='top', 
        #              bbox=dict(boxstyle='round', fc='w'))
        # ax2.annotate(f't_a: {temp_a} K', xy=xy_pos_1, xycoords='axes fraction',
        #              size=10, ha='left', va='top', 
        #              bbox=dict(boxstyle='round', fc='w'))
        # ax2.annotate(f't_b: {temp_b} K', xy=xy_pos_2, xycoords='axes fraction',
        #              size=10, ha='left', va='top', 
        #              bbox=dict(boxstyle='round', fc='w'))
        # ax2.annotate(f't_c: {temp_c} K', xy=xy_pos_3, xycoords='axes fraction',
        #              size=10, ha='left', va='top', 
        #              bbox=dict(boxstyle='round', fc='w'))
        # ax2.annotate(f't_d: {temp_d} K', xy=xy_pos_4, xycoords='axes fraction',
        #              size=10, ha='left', va='top', 
        #              bbox=dict(boxstyle='round', fc='w'))
        
        xy_pos_0_2 = (0.45, -0.6)
        xy_pos_1_2 = (0.45, -0.2)
        xy_pos_2_2 = (0.45, -0.3)
        xy_pos_3_2 = (0.45, -0.4)
        xy_pos_4_2 = (0.45, -0.5)
        
        ax1.annotate(f't_e: {"{0:.2f}".format(temp_htr)} K', xy=xy_pos_0_2, xycoords='axes fraction',
                     size=10, ha='left', va='top', 
                     bbox=dict(boxstyle='round', fc='w'))
        ax1.annotate(f't_a: {"{0:.2f}".format(temp_a)} K', xy=xy_pos_1_2, xycoords='axes fraction',
                     size=10, ha='left', va='top', 
                     bbox=dict(boxstyle='round', fc='w'))
        ax1.annotate(f't_b: {"{0:.2f}".format(temp_b)} K', xy=xy_pos_2_2, xycoords='axes fraction',
                     size=10, ha='left', va='top', 
                     bbox=dict(boxstyle='round', fc='w'))
        ax1.annotate(f't_c: {"{0:.2f}".format(temp_c)} K', xy=xy_pos_3_2, xycoords='axes fraction',
                     size=10, ha='left', va='top', 
                     bbox=dict(boxstyle='round', fc='w'))
        ax1.annotate(f't_d: {"{0:.2f}".format(temp_d)} K', xy=xy_pos_4_2, xycoords='axes fraction',
                     size=10, ha='left', va='top', 
                     bbox=dict(boxstyle='round', fc='w'))
        
        plt.draw()
        append_to_csv(dataFile, data_tmp)

        return l_xp, l_yp, l_ids_x, l_ids_y, #l_t_htr, l_t_a, l_t_b, l_t_c, l_t_d

def setup_plots():
    gs = fig.add_gridspec(3, 1, wspace=0, hspace=0.1)
    ax1 = fig.add_subplot(gs[:-1, 0])
    # ax2 = fig.add_subplot(gs[-1, 0])

    ax1.grid()
    # ax2.grid()

    ax1.set_ylabel(r'pos (um)')
    ax1.tick_params(axis='x', labelrotation=45)
    # ax1.tick_params(labelbottom=False)
    ax1.set_xlabel('Elapsed Time (s)')
    
    # ax2.set_xlabel('Elapsed Time (s)')
    # ax2.set_ylabel(r'temp')
    # ax2.tick_params(axis='x', labelrotation=45)
    
    # return ax1, ax2
    return ax1 

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
    
    mag = MagSensor(SER_MAG, 1, 'passive') if (GET_COUNTS or GET_MAG) else None

    print(f'dataFile: {dataFile}')
    append_to_csv(dataFile, header)

    # Create figure for plotting
    fig = plt.figure()
    # ax1, ax2 = setup_plots()
    ax1 = setup_plots()

    t = [] 
    t_htr, t_a, t_b, t_c, t_d = [], [], [], [], [] 
    x_sin, x_cos, x_pos = [], [], []
    y_sin, y_cos, y_pos = [], [], []
    ids_x, ids_y, ids_z = [], [], []

    # Draw x and y lists
    marker_fmt = '.'
    ms_fmt = 10
    lw_fmt = 1

    # l_t_htr, = ax2.plot(t, t_htr, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='blue')
    # l_t_a,   = ax2.plot(t, t_a, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='green')
    # l_t_b,   = ax2.plot(t, t_b, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='orange')
    # l_t_c,   = ax2.plot(t, t_c, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='red')
    # l_t_d,   = ax2.plot(t, t_d, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='purple')

    l_xp,    = ax1.plot(t, x_pos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='red')
    l_ids_x, = ax1.plot(t, ids_x, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='orange')
    l_yp,    = ax1.plot(t, y_pos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='blue')
    l_ids_y, = ax1.plot(t, ids_y, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='green')

    # Get starting values
    start_time = dt.datetime.now()
    
    start_t_htr = get_Lakeshore_temp(ser_htr) if SER_HTR else None
    start_t_a, start_t_b, start_t_c, start_t_d = ls_366.get_all_kelvin_reading()[:4]
    
    (warningNo, start_1, start_2, start_3) = ids.displacement.getAbsolutePositions() if GET_IDS else (None, 0, 0, 0)
    # start_pos_data = mag.get_real_position() if GET_MAG else (0,0) 
    difcs_msg = mag.get_difcs_msg(pos=True)
    start_x_pos = difcs_msg["x_pos"]
    start_y_pos = difcs_msg["y_pos"]
    print(start_x_pos)
    try:
        # Set up plot to call animate() function periodically
        ani = animation.FuncAnimation(fig, 
                                      animate, 
                                      fargs=(t, t_htr, t_a, t_b, t_c, t_d, x_sin, x_cos, y_sin, y_cos, x_pos, y_pos, ids_x, ids_y, ids_z), 
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
        print("closing")
        sys.exit(0)