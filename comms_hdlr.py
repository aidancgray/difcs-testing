import time
import serial
from serial.serialutil import SEVENBITS, PARITY_ODD, STOPBITS_ONE
from difcs import DiFCS
import IDSlib.IDS as IDS
from lakeshore import Model336

class CommsHandler:
    def __init__(self, logger, q_data, q_send, q_recv, closing_event, ls321_port, difcs_port, ids_ip):
        self.logger = logger
        self.q_data = q_data
        self.q_send = q_send
        self.q_recv = q_recv
        self.closing_event = closing_event

        self.logger.info('starting Comms Handler ...')

        self.ls_366 = Model336()
        self.ls_321 = serial.Serial(port=ls321_port, 
                                    baudrate=1200, 
                                    timeout=1, 
                                    bytesize=SEVENBITS,
                                    parity=PARITY_ODD,
                                    stopbits=STOPBITS_ONE)
        
        self.difcs = DiFCS(difcs_port)
        
        self.ids = IDS.Device(ids_ip) 
        self.ids.connect()
        
        if not self.ids.displacement.getMeasurementEnabled():
            self.ids.system.setInitMode(0) # enable high accuracy mode
            self.ids.system.startMeasurement()
            while not self.ids.displacement.getMeasurementEnabled():
                time.sleep(1)
    
    def start_comms(self):
        self.logger.info('... Comms Handler started')
        try:
            while not self.closing_event.is_set():
                if not self.q_send.empty():
                    new_send = self.q_send.get()

                    self.logger.debug(f'new_send={new_send}')
        except KeyboardInterrupt:
            self.closing_event.set()

    def get_LS_321_temp(self):
        msg = ('CDAT?').encode()
        self.ls_321.write(msg)
        resp = self.ls_321.readline()
        ls_321_temp = resp.decode()

        ls_321_temp = ls_321_temp.split(' ')[0]
        try:
            ls_321_temp = float(ls_321_temp)
        except ValueError:
            return -999
        else:
            return ls_321_temp
