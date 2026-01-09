from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from shiny import reactive
from shiny.express import render, ui
from shiny.session import session_context

DATA_PATH = "C:/Users/Aidan/Documents/MIRMOS/DIFCs_Testing/"
DATA_LIMIT = 100
data_dir = Path(DATA_PATH)
data_file = max([f for f in data_dir.glob("*.csv")], key=lambda item: item.stat().st_ctime)

ui.page_opts(fillable=True)

{"class": "bslib-page-dashboard"}
with session_context(None):

    @reactive.file_reader(data_dir / data_file)
    def logs_df():
        return pd.read_csv(data_dir / data_file)

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

            raw_df = logs_df()
            t = raw_df["time"]
            x_pos = raw_df["mag_x_0"]
            y_pos = raw_df["mag_y_0"]
            ids_x = raw_df["ids_x_0"]
            ids_y = raw_df["ids_y_0"]

            t = t[-DATA_LIMIT:]
            x_pos = x_pos[-DATA_LIMIT:]
            y_pos = y_pos[-DATA_LIMIT:]
            ids_x = ids_x[-DATA_LIMIT:]
            ids_y = ids_y[-DATA_LIMIT:]

            l_xp,    = ax1.plot(t, x_pos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='red')
            l_yp,    = ax1.plot(t, y_pos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='blue')
            
            l_ids_x, = ax1.plot(t, ids_x, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='orange')
            l_ids_y, = ax1.plot(t, ids_y, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='green')
        
            return fig

    with ui.card():        
        @render.data_frame
        def df():
            raw_df = logs_df()
            x_pos_df = raw_df["mag_x_0"].iloc[-1]
            y_pos_df = raw_df["mag_y_0"].iloc[-1]
            x_ids_df = raw_df["ids_x_0"].iloc[-1]
            y_ids_df = raw_df["ids_y_0"].iloc[-1]
            try:
                sp_df    = raw_df["setpoint"].iloc[-1]
            except:  # noqa: E722
                df = pd.DataFrame(np.array([
                    ['MAG X', "{0:.3f}".format(x_pos_df)],
                    ['IDS X', "{0:.3f}".format(x_ids_df)],
                    ['MAG Y', "{0:.3f}".format(y_pos_df)],
                    ['IDS Y', "{0:.3f}".format(y_ids_df)],
                ]), columns=['KEY', 'VALUE'])    
            else:
                df = pd.DataFrame(np.array([
                    ['SETPOINT', "{0:.3f}".format(sp_df)],
                    ['MAG X', "{0:.3f}".format(x_pos_df)],
                    ['IDS X', "{0:.3f}".format(x_ids_df)],
                    ['MAG Y', "{0:.3f}".format(y_pos_df)],
                    ['IDS Y', "{0:.3f}".format(y_ids_df)],
                ]), columns=['KEY', 'VALUE'])
            
            return df
