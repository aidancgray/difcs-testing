from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from shiny import reactive
from shiny.express import render, ui
from shiny.session import session_context


datafile = 'difcs-data.csv'
app_dir = Path(__file__).parent

ui.page_opts(fillable=True)

{"class": "bslib-page-dashboard"}
with session_context(None):

    @reactive.file_reader(app_dir / datafile)
    def logs_df():
        return pd.read_csv(app_dir / datafile)

with ui.layout_columns(col_widths=[ 10, 2],):
    with ui.card():
        # ui.card_header("Plots")
        
        @render.plot(alt='Data Plot')
        def plot_data():
            # fig, ax1 = plt.subplots()
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
            x_pos = raw_df["x_pos"]
            y_pos = raw_df["y_pos"]
            l_xp,    = ax1.plot(t, x_pos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='red')
            l_yp,    = ax1.plot(t, y_pos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='blue')
            
            ids_x = raw_df["ids_x"]
            ids_y = raw_df["ids_y"]
            l_ids_x, = ax1.plot(t, ids_x, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='orange')
            l_ids_y, = ax1.plot(t, ids_y, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='green')
        
            return fig
            

    with ui.card():
        # ui.card_header("Data")
        
        @render.data_frame
        def df():
            raw_df = logs_df()
            x_pos_df = raw_df["x_pos"].iloc[-1]
            y_pos_df = raw_df["y_pos"].iloc[-1]
            x_ids_df = raw_df["ids_x"].iloc[-1]
            y_ids_df = raw_df["ids_y"].iloc[-1]

            df = pd.DataFrame(np.array([
                ['MAG X', "{0:.3f}".format(x_pos_df)],
                ['IDS X', "{0:.3f}".format(x_ids_df)],
                ['MAG Y', "{0:.3f}".format(y_pos_df)],
                ['IDS Y', "{0:.3f}".format(y_ids_df)],
            ]), columns=['KEY', 'VALUE'])
            
            # return render.DataTable(df)
            return df

# @reactive.calc
# def current():
#     return logs_df().iloc[-1]


# _ = session.on_ended(process.kill)
