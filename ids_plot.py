import os
import sys
import time
import csv
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import IDSlib.IDS as IDS

GET_IDS = True

IDS_IP = "172.16.1.198"
ANIM_INTER = 50
DATA_LIMIT = 100

if os.name == "posix":
    DATA_PATH = "/Users/aidancgray/Documents/MIRMOS/DiFCS/testdata/"
else: 
    DATA_PATH = "C:/Users/Aidan/Documents/MIRMOS/DIFCs_Testing/"

DEBUG = sys.argv[1] if len(sys.argv) > 1 else None

# This function is called periodically from FuncAnimation
def animate(i, t, ids_x, ids_y, ids_z):
    try:
        (warningNo, pos_1_pm, pos_2_pm, pos_3_pm) = ids.displacement.getAbsolutePositions() if GET_IDS else (None, 0, 0, 0)
        abs_1_um = float(pos_1_pm) / 1000000
        abs_2_um = float(pos_2_pm) / 1000000
        abs_3_um = float(pos_3_pm) / 1000000
        
        pos_1_um =  -abs_1_um + (float(start_1) /  1000000)
        pos_2_um =   abs_2_um - (float(start_2) /  1000000)
        pos_3_um =   abs_3_um - (float(start_3) /  1000000)

        # Add x and y to lists
        meas_time = float("{0:.3f}".format((dt.datetime.now() - start_time).total_seconds()))
        
        data_tmp = [meas_time, 
                    abs_1_um,
                    abs_2_um,
                    abs_3_um,
                    ]

        t.append(meas_time)

        ids_x.append(pos_1_um)
        ids_y.append(pos_2_um)
        ids_z.append(pos_3_um)

        # Limit x and y lists to DATA_LIMIT items
        t = t[-DATA_LIMIT:]

        ids_x = ids_x[-DATA_LIMIT:]
        ids_y = ids_y[-DATA_LIMIT:]
        ids_z = ids_z[-DATA_LIMIT:]
    
    except ValueError:
        return None

    else:
        fig.clear()
        ax1 = setup_plots()

        # Draw x and y lists
        marker_fmt = '.'
        ms_fmt = 5
        lw_fmt = 1

        l_ids_x, = ax1.plot(t, ids_x, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='red')
        l_ids_y, = ax1.plot(t, ids_y, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='blue')
        l_ids_z, = ax1.plot(t, ids_z, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='green')

        xy_pos_0 = (1.01, 0.95)
        xy_pos_1 = (1.01, 0.70)
        xy_pos_2 = (1.01, 0.45)
        xy_pos_3 = (1.01, 0.20)
        xy_pos_4 = (1.01, -0.05)
        
        ax1.annotate(f'x: {"{0:.3f}".format(pos_1_um)}', xy=xy_pos_0, xycoords='axes fraction',
                     size=10, ha='left', va='top', color='red', 
                     bbox=dict(boxstyle='round', fc='w'))
        ax1.annotate(f'y: {"{0:.3f}".format(pos_2_um)}', xy=xy_pos_1, xycoords='axes fraction',
                     size=10, ha='left', va='top', color='blue', 
                     bbox=dict(boxstyle='round', fc='w'))
        ax1.annotate(f'z: {"{0:.3f}".format(pos_3_um)}', xy=xy_pos_2, xycoords='axes fraction',
                     size=10, ha='left', va='top', color='green', 
                     bbox=dict(boxstyle='round', fc='w'))
        
        plt.draw()
        if (DEBUG != 'no-write'):
            append_to_csv(dataFile, data_tmp)

        return l_ids_x, l_ids_y, l_ids_z

def setup_plots():
    # gs = fig.add_gridspec(1, 1, wspace=0, hspace=0.1)
    ax1 = fig.add_subplot()
    ax1.grid()

    ax1.set_ylabel(r'pos (um)')
    ax1.tick_params(axis='x', labelrotation=45)
    ax1.set_xlabel('Elapsed Time (s)')

    return ax1 

def append_to_csv(dataFile, data):
    with open(f'{dataFile}', 'a', newline='') as fd:
        writer = csv.writer(fd)
        writer.writerow(data)

if __name__ == "__main__":
    if (DEBUG != 'no-write'):
        dataFile = f"{DATA_PATH}{dt.datetime.now().strftime('%d%m%Y_%H-%M-%S')}.csv"
        header = ['time', 
                'ids_x', 
                'ids_y',
                'ids_z',]
        print(f'dataFile: {dataFile}')
        append_to_csv(dataFile, header)

    if GET_IDS:
        ids = IDS.Device(IDS_IP) 
        ids.connect()
        
        if not ids.displacement.getMeasurementEnabled():
            ids.system.setInitMode(0) # enable high accuracy mode
            ids.system.startMeasurement()
            while not ids.displacement.getMeasurementEnabled():
                time.sleep(1)


    # Create figure for plotting
    fig = plt.figure()
    ax1 = setup_plots()

    t = [] 
    ids_x, ids_y, ids_z = [], [], []

    # Draw x and y lists
    marker_fmt = '.'
    ms_fmt = 10
    lw_fmt = 1

    l_ids_x, = ax1.plot(t, ids_x, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='red')
    l_ids_y, = ax1.plot(t, ids_y, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='blue')
    l_ids_z, = ax1.plot(t, ids_z, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='green')

    # Get starting values
    start_time = dt.datetime.now()
    
    (warningNo, start_1, start_2, start_3) = ids.displacement.getAbsolutePositions() if GET_IDS else (None, 0, 0, 0)
    
    try:
        # Set up plot to call animate() function periodically
        ani = animation.FuncAnimation(fig, 
                                      animate, 
                                      fargs=(t, ids_x, ids_y, ids_z), 
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