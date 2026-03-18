from pathlib import Path
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
from io import StringIO
from shiny import reactive
from shiny.express import render, ui
from shiny.session import session_context

if os.name == "posix":
    DATA_PATH = "/Users/aidancgray/Documents/MIRMOS/DiFCS/testdata/"
else:
    DATA_PATH = "C:/Users/Aidan/Documents/MIRMOS/DIFCs_Testing/"
DATA_LIMIT = 50
data_dir = Path(DATA_PATH)
data_file = max([f for f in data_dir.glob("*.csv")], key=lambda item: item.stat().st_ctime)

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
        
            ax1.set_ylabel(r'ADC (counts)')
            ax1.tick_params(axis='x', labelrotation=45)
            ax1.set_xlabel('Elapsed Time (s)')
            
            # Draw x and y lists
            marker_fmt = '.'
            ms_fmt = 5
            lw_fmt = 1

            raw_df = data_df()
            t = raw_df["time"]
            ch_0_sin = raw_df["ch_0_sin"]
            ch_0_cos = raw_df["ch_0_cos"]
            ch_1_sin = raw_df["ch_1_sin"]
            ch_1_cos = raw_df["ch_1_cos"]

            t = t[-DATA_LIMIT:]
            ch_0_sin = ch_0_sin[-DATA_LIMIT:]
            ch_0_cos = ch_0_cos[-DATA_LIMIT:]
            ch_1_sin = ch_1_sin[-DATA_LIMIT:]
            ch_1_cos = ch_1_cos[-DATA_LIMIT:]

            l_ch0s,    = ax1.plot(t, ch_0_sin, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='red')
            l_ch0c,    = ax1.plot(t, ch_0_cos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='orange')
            l_ch1s,    = ax1.plot(t, ch_1_sin, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='blue')
            l_ch1c,    = ax1.plot(t, ch_1_cos, marker=marker_fmt, markersize=ms_fmt, linewidth=lw_fmt, color='green')
        
            return fig

    with ui.card():        
        @render.data_frame
        def df():
            raw_df = data_df()
            ch_0_sin_df = raw_df["ch_0_sin"].iloc[-1]
            ch_0_cos_df = raw_df["ch_0_cos"].iloc[-1]
            ch_1_sin_df = raw_df["ch_1_sin"].iloc[-1]
            ch_1_cos_df = raw_df["ch_1_cos"].iloc[-1]
            
            df = pd.DataFrame(np.array([
                ['CH 0 SIN', "{0:.3f}".format(ch_0_sin_df)],
                ['CH 0 COS', "{0:.3f}".format(ch_0_cos_df)],
                ['CH 1 SIN', "{0:.3f}".format(ch_1_sin_df)],
                ['CH 1 COS', "{0:.3f}".format(ch_1_cos_df)],
            ]), columns=['KEY', 'VALUE'])    
            
            return df
