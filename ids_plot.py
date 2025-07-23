import sys
import time
import csv
import serial
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from math import floor
from serial.serialutil import SEVENBITS, PARITY_ODD, STOPBITS_ONE
import IDS

DATA_PATH = "/Users/aidancgray/Documents/MIRMOS/DiFCS/attocube/"
IDS_IP = "172.16.1.198"
ANIM_INTER = 500
DATA_LIMIT = 300
SER_DIF = '/dev/tty.usbserial-A506NMAT'
SER_HTR = '/dev/tty.usbserial-14420'

DEBUG = sys.argv[1] if len(sys.argv) > 1 else None

# This function is called periodically from FuncAnimation
def animate(i, xs, tds, ths, dys):
    # Get temp and position data
    temp_dif = get_Lakeshore_temp(ser_dif) if SER_DIF else None
    temp_htr = get_Lakeshore_temp(ser_htr) if SER_HTR else None

    try:
        warningNo, pos_1_pm, pos_2_pm, pos_3_um = ids.displacement.getAbsolutePositions()

        abs_1_um = float(pos_1_pm) / 1000000
        abs_2_um = float(pos_2_pm) / 1000000

        pos_1_um = float(pos_1_pm - start_1) / 1000000
        pos_2_um = float(pos_2_pm - start_2) / 1000000

        delta_length_um = -1*(pos_1_um + pos_2_um)

        # Add x and y to lists
        meas_time = float("{0:.3f}".format((dt.datetime.now() - start_time).total_seconds()))
        
        data_tmp = [meas_time, 
                    temp_dif if temp_dif else '--', 
                    temp_htr if temp_htr else '--', 
                    abs_1_um, 
                    abs_2_um]

        xs.append(floor(meas_time))
        tds.append(temp_dif) if temp_dif else None
        ths.append(temp_htr) if temp_htr else None 
        dys.append(delta_length_um)

        # Limit x and y lists to DATA_LIMIT items
        xs = xs[-DATA_LIMIT:]
        tds = tds[-DATA_LIMIT:]
        ths = ths[-DATA_LIMIT:]
        dys = dys[-DATA_LIMIT:]
    
    except ValueError:
        return None

    else:
        fig.clear()  # clear
        ax1, ax2, ax3 = setup_plots()

        # Draw x and y lists
        marker_fmt = '.'
        ms_fmt = 5
        lw_fmt = 1
        if SER_DIF:
            linetd, = ax1.plot(xs, tds, marker=marker_fmt, markersize=ms_fmt, 
                               linewidth=lw_fmt, color='orange')
        if SER_HTR:
            lineth, = ax2.plot(xs, ths, marker=marker_fmt, markersize=ms_fmt, 
                               linewidth=lw_fmt, color='purple')
        line1, = ax3.plot(xs, dys, marker=marker_fmt, markersize=ms_fmt, 
                          linewidth=lw_fmt, color='blue')

        if SER_DIF:
            xy_pos_td = (1.01, 0.95)
            ax1.annotate(f'{temp_dif} K', xy=xy_pos_td, xycoords='axes fraction',
                         size=10, ha='left', va='top',
                         bbox=dict(boxstyle='round', fc='w'))
        if SER_HTR:
            xy_pos_th = (1.01, 0.95)
            ax2.annotate(f'{temp_htr} K', xy=xy_pos_th, xycoords='axes fraction',
                         size=10, ha='left', va='top',
                         bbox=dict(boxstyle='round', fc='w'))
        
        xy_pos = (1.01, 0.95)
        xy_pos_time = (1.01, 0.70)
        ax3.annotate(f'{delta_length_um} um', xy=xy_pos, xycoords='axes fraction',
                     size=10, ha='left', va='top',
                     bbox=dict(boxstyle='round', fc='w'))
        ax3.annotate(f'{floor(meas_time)} s', xy=xy_pos_time, xycoords='axes fraction',
                     size=10, ha='left', va='top',
                     bbox=dict(boxstyle='round', fc='w'))
        plt.draw()
        append_to_csv(dataFile, data_tmp)

        return line1, linetd if SER_DIF else None, lineth if SER_HTR else None

def setup_plots():
    gs = fig.add_gridspec(3, 1, wspace=0, hspace=0.1)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, 0])
    ax3 = fig.add_subplot(gs[2, 0])

    ax1.grid()
    ax2.grid()
    ax3.grid()

    # axt.set_title('Axes Positions vs Time')
    ax1.set_ylabel('Piezo Temp (K)')
    ax1.tick_params(labelbottom=False)
    
    ax2.set_ylabel('Coldplate Temp (K)')
    ax2.tick_params(labelbottom=False)
    
    ax3.set_xlabel('Elapsed Time (s)')
    ax3.set_ylabel(r'$\Delta$Piezo Length (um)')
    ax3.tick_params(axis='x', labelrotation=45)
    
    return ax1, ax2, ax3

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
    header = ['time', 'temp_dif', 'temp_htr', 'axis_1', 'axis_2']
    if SER_HTR and SER_DIF:
        ser_htr = serial.Serial(port=SER_HTR, 
                                baudrate=1200, 
                                timeout=1, 
                                bytesize=SEVENBITS,
                                parity=PARITY_ODD,
                                stopbits=STOPBITS_ONE)
    
        ser_dif = serial.Serial(port=SER_DIF, 
                                baudrate=1200, 
                                timeout=1, 
                                bytesize=SEVENBITS,
                                parity=PARITY_ODD,
                                stopbits=STOPBITS_ONE)
    elif SER_DIF:
        ser_dif = serial.Serial(port=SER_DIF, 
                                baudrate=1200, 
                                timeout=1, 
                                bytesize=SEVENBITS,
                                parity=PARITY_ODD,
                                stopbits=STOPBITS_ONE)
    elif SER_HTR:
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

    print(f'dataFile: {dataFile}')
    append_to_csv(dataFile, header)

    # Create figure for plotting
    fig = plt.figure()
    ax1, ax2, ax3 = setup_plots()

    xs = []
    tds = []
    ths = []
    dys = []

    # Draw x and y lists
    marker_fmt = '.'
    ms_fmt = 10
    lw_fmt = 1
    if SER_DIF:
        linetd, = ax1.plot(xs, tds, marker=marker_fmt, markersize=ms_fmt, 
                           linewidth=lw_fmt, color='orange')
    if SER_HTR:
        lineth, = ax2.plot(xs, ths, marker=marker_fmt, markersize=ms_fmt, 
                           linewidth=lw_fmt, color='purple')
    line1, = ax3.plot(xs, dys, marker=marker_fmt, markersize=ms_fmt, 
                      linewidth=lw_fmt, color='blue')

    start_time = dt.datetime.now()
    warningNo, start_1, start_2, start_3 = ids.displacement.getAbsolutePositions()
    start_t = get_Lakeshore_temp(ser_dif) if SER_DIF else None

    # Set up plot to call animate() function periodically
    ani = animation.FuncAnimation(fig, 
                                    animate, 
                                    fargs=(xs, tds, ths, dys), 
                                    interval=ANIM_INTER,
                                    cache_frame_data=False)
    plt.show()
    ids.close()
