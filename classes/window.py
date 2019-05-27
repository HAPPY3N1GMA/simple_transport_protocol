#! /usr/bin/env python3.6

import threading
from classes import defines,protocol,threads,message,timer,log

class STPWindow(object):
    ''' STP Message Window '''
    def __init__(self):
        ''' Initialises an STP Window Object '''
        self._msgQueue = None
        self._numWindowPanes = 0
        self._window = {}
        self._minPane = 0
        self._maxPane = 0
        self.lock = threading.RLock()


    def set_minPane(self,value:int):
        ''' set minPane value '''
        with self.lock:
            self._minPane = value 
        return value


    def set_maxPane(self,value:int):
        ''' set mAPane value '''
        with self.lock:
            self._maxPane = value 
        return value


    def set_msgQueue(self,queue:object):
        ''' set msgQueue object '''
        with self.lock:
            self._msgQueue = queue


    def set_numWindowPanes(self,value:int):
        ''' set minPane value '''
        with self.lock:
            self._numWindowPanes = value


    def get_numWindowPanes(self):
        ''' set number of window panes '''
        return self._numWindowPanes


    def get_minPane(self):
        ''' get minPane value '''
        return self._minPane


    def get_maxPane(self):
        ''' get maxPane value '''
        return self._maxPane


    def get_window(self):
        ''' get window object '''
        return self._window


    def set_window_status(self,key,value):
        ''' set window pane status '''
        with self.lock:
            self.get_window()[key] = value
        return value 


    def get_window_status(self,key):
        ''' get window pane value '''
        if key in self._window:
                return self.get_window()[key]
        return defines.Status.DEFAULT


    def get_msgQueue(self):
        ''' get msgQueue object '''
        return self._msgQueue


    def msg_sent(self,key):
        ''' returns True/False if msg (key) has been sent to, or received by server '''
        status = self.get_window_status(key)
        if status == defines.Status.DEFAULT:
            return False
        return True


    def msg_received(self,key):
        ''' returns True/False if msg (key) has been received (ie ACK from sender received) '''
        status = self.get_window_status(key)
        if status in (defines.Status.RECEIVED,defines.Status.RECEIVED_1,defines.Status.RECEIVED_2):
            return True
        return False
