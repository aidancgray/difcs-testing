from pathlib import Path
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
from io import StringIO
from shiny import reactive
from shiny.express import render, ui, input
from shiny.session import session_context

if os.name == "posix":
    DATA_PATH = "/Users/aidancgray/Documents/MIRMOS/DiFCS/testdata/"
else:
    DATA_PATH = "C:/Users/Aidan/Documents/MIRMOS/DIFCs_Testing/"
data_dir = Path(DATA_PATH)
data_file = max([f for f in data_dir.glob("*.csv")], key=lambda item: item.stat().st_ctime)

DATA_LIMIT = 50

zeros = {'x': 0, 
         'y': 0, 
         'z': 0}

ui.page_opts(fillable=True)

{"class": "bslib-page-dashboard"}
with session_context(None):

    @reactive.file_reader(data_dir / data_file)
    def data_df():
        fname = data_dir / data_file
        with open(fname, 'r') as f:
            q = [ f.readline() ] 
            q.extend(deque(f, DATA_LIMIT)) 
        data_df = pd.read_csv(StringIO(''.join(q)))
        return data_df

with ui.layout_columns(col_widths=[ 10, 2],):
    with ui.card():
        @render.plot(alt='Data Plot')
        def plot_data():
            fig = plt.figure()
            gs = fig.add_gridspec(1, 1, wspace=0, hspace=0)
            ax1 = fig.add_subplot(gs[0, 0])
            ax1.grid()
        
            ax1.set_ylabel(r'pos (um)')
            ax1.tick_params(axis='x', labelrotation=45)
            ax1.set_xlabel('Elapsed Time (s)')
            
            # Draw x and y lists
            marker_fmt = '.'
            ms_fmt = 5
            lw_fmt = 1

            raw_df = data_df()
            t = raw_df["time"]
            ids_x = raw_df["ids_x_0"] - zeros['x']
            ids_y = raw_df["ids_y_0"] - zeros['y']
            ids_z = raw_df["ids_z_0"] - zeros['z']

            t = t[-DATA_LIMIT:]
            ids_x = ids_x[-DATA_LIMIT:]
            ids_y = ids_y[-DATA_LIMIT:]
            ids_z = ids_z[-DATA_LIMIT:]

            l_ids_x, = ax1.plot(t, ids_x, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='red', label='IDS X')
            l_ids_y, = ax1.plot(t, ids_y, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='blue', label='IDS Y')
            l_ids_z, = ax1.plot(t, ids_z, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='green', label='IDS Z')
            ax1.legend(loc='upper right')

            return fig

    with ui.card():
        ui.input_action_button("action_button", "ZERO AXES")
        @render.text
        @reactive.event(input.action_button)
        def zero_axes():
            global zeros
            raw_df = data_df()
            zeros['x'] = raw_df["ids_x_0"].iloc[-1]
            zeros['y'] = raw_df["ids_y_0"].iloc[-1]
            zeros['z'] = raw_df["ids_z_0"].iloc[-1] 
            return None

        @render.data_frame
        def df():
            raw_df = data_df()
            x_ids_df = raw_df["ids_x_0"].iloc[-1] - zeros['x']
            y_ids_df = raw_df["ids_y_0"].iloc[-1] - zeros['y']
            z_ids_df = raw_df["ids_z_0"].iloc[-1] - zeros['z']
            try:
                sp_df    = raw_df["setpoint"].iloc[-1]
                dac_x_df    = raw_df["dac_x"].iloc[-1]
                dac_y_df    = raw_df["dac_y"].iloc[-1]
            except:  # noqa: E722
                df = pd.DataFrame(np.array([
                    ['IDS X', "{0:.3f}".format(x_ids_df)],
                    ['IDS Y', "{0:.3f}".format(y_ids_df)],
                    ['IDS Z', "{0:.3f}".format(z_ids_df)],
                ]), columns=['KEY', 'VALUE'])    
            else:
                df = pd.DataFrame(np.array([
                    ['SETPOINT', "{0:.3f}".format(sp_df)],
                    ['DAC X', dac_x_df],
                    ['IDS X', "{0:.3f}".format(x_ids_df)],
                    ['DAC Y', dac_y_df],
                    ['IDS Y', "{0:.3f}".format(y_ids_df)],
                    ['IDS Z', "{0:.3f}".format(z_ids_df)],
                ]), columns=['KEY', 'VALUE'])
            
            return df
