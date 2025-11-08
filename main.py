import sys, os
import logging
import argparse
import shlex

from signal import SIGINT, SIGTERM
from multiprocessing import Process, Queue, Event

from data_plotter import RealtimePlot
from comms_hdlr import CommsHandler


LOGGER_NAME = 'difcs_plot'
IDS_IP = "172.16.1.198"

if os.name == "posix":
    DATA_PATH = "/Users/aidancgray/Documents/MIRMOS/DiFCS/testdata/"
    SER_DIFCS = "/dev/tty.usbserial-B001A17V"
    SER_LS321 = "/dev/tty.usbserial-A506NMAT"
else: 
    DATA_PATH = "C:/Users/Aidan/Documents/MIRMOS/DIFCs_Testing/"
    SER_DIFCS = 'COM6'
    SER_LS321 = 'COM10'

def run_gui(q_comms_in, q_comms_out, closing_event, opts):
    logger = logging.getLogger(LOGGER_NAME)

def run_comms_hdlr(q_plot_data, q_comms_in, q_comms_out, closing_event):
    logger = logging.getLogger(LOGGER_NAME)

    commhdlr = CommsHandler(logger.getChild('comms_hdlr'),
                            q_plot_data,
                            q_comms_in,
                            q_comms_out,
                            closing_event,
                            ls321_port=SER_LS321,
                            difcs_port=SER_DIFCS,
                            ids_ip=IDS_IP,)
    
    commhdlr.start_comms()

def run_data_display(q_plot_data, closing_event, opts):
    logger = logging.getLogger(LOGGER_NAME)

    rtplot = RealtimePlot(logger.getChild('data_plot'), 
                          q_plot_data, 
                          closing_event, 
                          opts,)
    
    rtplot.start_plotter()

def start_gui(q_comms_in, q_comms_out, closing_event, opts):
    try:
        run_gui(q_comms_in, q_comms_out, closing_event, opts)
    except RuntimeError as exc:
        print(exc)
    finally:
        pass

def start_sender(q_plot_data, q_comms_in, q_comms_out, closing_event):
    try:
        run_comms_hdlr(q_plot_data, q_comms_in, q_comms_out, closing_event)
    except RuntimeError as exc:
        print(exc)
    finally:
        pass

def start_receiver(q_plot_data, closing_event, opts):
    try:
        run_data_display(q_plot_data, closing_event, opts)
    except RuntimeError as exc:
        print(exc)
    finally:
        pass

def argparser(argv):
    if argv is None:
        argv = sys.argv[1:]
    if isinstance(argv, str):
        argv = shlex.split(argv)

    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('--logLevel', type=int, default=logging.INFO,
                        help='logging threshold. 10=debug, 20=info, 30=warn')
    opts = parser.parse_args(argv)

    return opts

def main(argv=None):
    opts = argparser(argv)    

    # create logger
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(opts.logLevel)
    # create stream handler
    con_hdlr = logging.StreamHandler()
    con_hdlr.setLevel(opts.logLevel)
    # create formatter and add to handler
    log_format = '%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s'
    log_formatter = logging.Formatter(datefmt = '%Y-%m-%d | %H:%M:%S',
                                      fmt = log_format)
    con_hdlr.setFormatter(log_formatter)
    # add handler to logger
    logger.addHandler(con_hdlr)

    closing_event = Event()  # Event to signal closing of the receiver to the other process
    reset_event = Event()  # Event to signal the press of the reset button

    q_plot_data = Queue(maxsize=0)
    q_comms_in = Queue(maxsize=0)
    q_comms_out = Queue(maxsize=0)

    receiver = Process(target=start_receiver, args=(q_plot_data, closing_event, opts))
    sender = Process(target=start_sender, args=(q_plot_data, q_comms_in, q_comms_out, closing_event))
    gui = Process(target=start_gui, args=(q_comms_in, q_comms_out, closing_event, opts))

    receiver.start()
    sender.start()
    gui.start()
    try:
        receiver.join()
        sender.join()
        gui.join()
    except KeyboardInterrupt:
        closing_event.set()
        logger.info('~~~~~~ stopping main process ~~~~~~')

if __name__ == "__main__":
    main()