import sys
import time
import csv
import serial
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from math import floor, pi, atan
from serial.serialutil import SEVENBITS, EIGHTBITS, PARITY_ODD, PARITY_NONE, STOPBITS_ONE
import IDS


# DATA_PATH = "/Users/aidancgray/Documents/MIRMOS/DiFCS/mag-sensor/"
DATA_PATH = "C:/Users/Aidan/Documents/MIRMOS/DIFCs_Testing/"
IDS_IP = "172.16.1.198"
ANIM_INTER = 500
DATA_LIMIT = 30
SER_DIF = '/dev/tty.usbserial-A506NMAT'
SER_MAG = '/dev/tty.usbmodem586D0017611'

DEBUG = sys.argv[1] if len(sys.argv) > 1 else None

# This function is called periodically from FuncAnimation
def animate(i, xs, msin, mcos, mdeg, mums):
    # Get temp and position data
    temp_dif = get_Lakeshore_temp(ser_dif) if SER_DIF else None
    # temp_htr = get_Lakeshore_temp(ser_htr) if SER_HTR else None

    mag_rdout = get_mag_sensor_readout(ser_mag)
    while not mag_rdout:
        mag_rdout = get_mag_sensor_readout(ser_mag)
    mag_sin, mag_cos = mag_rdout
    mag_deg, mag_ums = get_mag_degrees(mag_sin, mag_cos)
    mag_ums_offset = mag_ums-start_mag_ums

    try:
        # Add x and y to lists
        meas_time = float("{0:.3f}".format((dt.datetime.now() - start_time).total_seconds()))
        
        data_tmp = [meas_time, 
                    temp_dif if temp_dif else '--', 
                    mag_sin, 
                    mag_cos,
                    mag_deg,
                    mag_ums]

        xs.append(floor(meas_time))
        msin.append(mag_sin)
        mcos.append(mag_cos)
        mums.append(mag_ums_offset)

        # Limit x and y lists to DATA_LIMIT items
        xs = xs[-DATA_LIMIT:]
        msin = msin[-DATA_LIMIT:]
        mcos = mcos[-DATA_LIMIT:]
        mums = mums[-DATA_LIMIT:]
    
    except ValueError:
        return None

    else:
        fig.clear()  # clear
        ax1, ax2 = setup_plots()

        # Draw x and y lists
        marker_fmt = '.'
        ms_fmt = 5
        lw_fmt = 1

        l_msin, = ax1.plot(xs, msin, marker=marker_fmt, markersize=ms_fmt, 
                            linewidth=lw_fmt, color='red')
        l_mcos, = ax1.plot(xs, mcos, marker=marker_fmt, markersize=ms_fmt, 
                            linewidth=lw_fmt, color='blue')
        l_mums, = ax2.plot(xs, mums, marker=marker_fmt, markersize=ms_fmt, 
                            linewidth=lw_fmt, color='green')
        
        xy_pos_0 = (1.01, 0.95)
        xy_pos_1 = (1.01, 0.70)
        xy_pos_2 = (1.01, 0.45)
        
        ax1.annotate(f'temp: {temp_dif}', xy=xy_pos_0, xycoords='axes fraction',
                     size=10, ha='left', va='top', 
                     bbox=dict(boxstyle='round', fc='w'))
        ax1.annotate(f'sin: {mag_sin}', xy=xy_pos_1, xycoords='axes fraction',
                     size=10, ha='left', va='top', 
                     bbox=dict(boxstyle='round', fc='w'))
        ax1.annotate(f'cos: {mag_cos}', xy=xy_pos_2, xycoords='axes fraction',
                     size=10, ha='left', va='top', 
                     bbox=dict(boxstyle='round', fc='w'))
        
        ax2.annotate(f'deg: {mag_deg}', xy=xy_pos_0, xycoords='axes fraction',
                     size=10, ha='left', va='top', 
                     bbox=dict(boxstyle='round', fc='w'))
        ax2.annotate(f'pos: {float("{0:.3f}".format(mag_ums_offset))} um', xy=xy_pos_1, xycoords='axes fraction',
                     size=10, ha='left', va='top',
                     bbox=dict(boxstyle='round', fc='w'))
        
        
        plt.draw()
        append_to_csv(dataFile, data_tmp)

        return l_msin, l_mcos, l_mums

def setup_plots():
    gs = fig.add_gridspec(2, 1, wspace=0, hspace=0.1)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, 0])

    ax1.grid()
    ax2.grid()

    ax1.set_ylabel(r'counts')
    ax1.tick_params(labelbottom=False)
    
    ax2.set_xlabel('Elapsed Time (s)')
    ax2.set_ylabel(r'microns')
    ax2.tick_params(axis='x', labelrotation=45)
    
    return ax1, ax2

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

def get_mag_sensor_readout(ser):
    ser.reset_input_buffer()
    resp = ser.readline()
    msg = resp.decode()
    if len(msg) > 0:
        if msg[0] == 'y':
            sin, cos = msg.split(',')
            sin = int(sin.split('= ')[1])
            cos = int(cos.split('= ')[1])
            return sin, cos
        else:
            return None
    else:
        return None

def get_mag_degrees(sin, cos):
    deg = float( 90 + (180/pi) * atan(float(sin) / float(cos)) )
    if cos < 0: deg += 180
    ums = 5.5556*deg
    deg = float("{0:.1f}".format(deg))
    ums = float("{0:.2f}".format(ums))
    return deg, ums

if __name__ == "__main__":
    dataFile = f"{DATA_PATH}{dt.datetime.now().strftime('%d%m%Y_%H-%M-%S')}.csv"
    header = ['time', 'temp', 'mag_sin', 'mag_cos', 'mag_deg', 'mag_um', 'axis_1']
    if SER_MAG and SER_DIF:
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
    elif SER_DIF:
        ser_dif = serial.Serial(port=SER_DIF, 
                                baudrate=1200, 
                                timeout=1, 
                                bytesize=SEVENBITS,
                                parity=PARITY_ODD,
                                stopbits=STOPBITS_ONE)
    elif SER_MAG:
        ser_mag = serial.Serial(port=SER_MAG, 
                                baudrate=128000, 
                                timeout=1, 
                                bytesize=EIGHTBITS,
                                parity=PARITY_NONE,
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
    ax1, ax2 = setup_plots()

    xs, msin, mcos, mdeg, mums, dy = [], [], [], [], [], []

    # Draw x and y lists
    marker_fmt = '.'
    ms_fmt = 10
    lw_fmt = 1

    l_msin, = ax1.plot(xs, msin, marker=marker_fmt, markersize=ms_fmt, 
                        linewidth=lw_fmt, color='red')
    l_mcos, = ax1.plot(xs, mcos, marker=marker_fmt, markersize=ms_fmt, 
                        linewidth=lw_fmt, color='blue')
    l_mums, = ax2.plot(xs, mums, marker=marker_fmt, markersize=ms_fmt, 
                        linewidth=lw_fmt, color='green')

    # Get starting values
    start_time = dt.datetime.now()
    mag_rdout = get_mag_sensor_readout(ser_mag)
    while not mag_rdout:
        mag_rdout = get_mag_sensor_readout(ser_mag)
    start_mag_sin, start_mag_cos = mag_rdout
    start_mag_deg, start_mag_ums = get_mag_degrees(start_mag_sin, start_mag_cos)
    start_t = get_Lakeshore_temp(ser_dif) if SER_DIF else None

    # Set up plot to call animate() function periodically
    ani = animation.FuncAnimation(fig, 
                                    animate, 
                                    fargs=(xs, msin, mcos, mdeg, mums), 
                                    interval=ANIM_INTER,
                                    cache_frame_data=False)
    
    manager = plt.get_current_fig_manager()
    manager.full_screen_toggle()
    plt.show()
