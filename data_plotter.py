import matplotlib.pyplot as plt
import matplotlib.animation as animation

class RealtimePlot():
    def __init__(self, logger, q_plot_data, closing_event, opts):
        self.logger = logger
        self.logger.info('starting Realtime Plot ...')
        
        self.q_plot_data = q_plot_data
        self.closing_event = closing_event

    def start_plotter(self):
        self.logger.info('... Realtime Plot started')
        try:
            while not self.closing_event.is_set():
                if not self.q_plot_data.empty():
                    new_data = self.q_plot_data.get()

                    self.logger.debug(f'new_data={new_data}')

        except KeyboardInterrupt:
            self.closing_event.set()