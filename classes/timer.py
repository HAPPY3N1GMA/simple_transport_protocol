#! /usr/bin/env python3.6

import threading
from threading import Timer
from classes import defines,protocol,threads,message,window,defines,log
import time, datetime



class STDTimer(object):
    ''' Timer Object '''
    def __init__(self):
        self._TimerLock = threading.RLock()
        self._EstimatedRTT = defines.ESTIMATEDRTT
        self._DevRTT = defines.DEVRTT
        self._TimeoutInterval = defines.TIMEOUT
        self._TimeoutStart = None
        self._Gamma = 0

        ''' RTT Estimation '''
        self._RTTStatus = False


    def get_Gamma(self):
        ''' get Timer gamma value '''
        return self._Gamma


    def set_Gamma(self,value=0):
        ''' set Timer gamma value '''
        with self._TimerLock:
            self._Gamma = value


    def get_Time(self):
        ''' get Timer current Time '''
        return datetime.datetime.now()


    def get_RTTStart(self):
        ''' get Timer RTT Start Time '''
        return self._RTTStart


    def set_RTTStart(self,timeIn):
        ''' set Timer RTT Start Time '''
        with self._TimerLock:
            self._RTTStart = timeIn


    def RTTRunning(self):
        ''' return True if RTT Estimation in progress '''
        return self._RTTStatus


    def get_TimeoutStart(self):
        ''' get Timer Time-Out Start Time '''
        return self._TimeoutStart


    def TimeoutStarted(self):
        ''' return True if Timeout Timer Started '''
        TimeoutStart = self.get_TimeoutStart()
        if TimeoutStart != None:
            return True
        return False


    def set_TimeoutStart(self,timeIn):
        ''' set Timer Time-Out Start Time '''
        with self._TimerLock:
            self._TimeoutStart = timeIn


    def TimeoutExpired(self):  
        ''' return True if Timer Time-Out has Expired'''
        TimeoutStart = self.get_TimeoutStart()
        if TimeoutStart != None:
            TimeoutExpired = self.secondToMillisecond((self.get_Time() - TimeoutStart).total_seconds())
            TimeoutInterval = self.get_timeoutInterval()
            if (TimeoutExpired >= TimeoutInterval):
                return True
        return False


    def startTimeoutTimer(self,startRTT = False):
        ''' start Timer Time-Out'''
        with self._TimerLock:
            self.set_TimeoutStart(self.get_Time())
            self._RTTStatus = startRTT


    def secondToMillisecond(self,timeIn):
        ''' convert seconds to milliseconds '''
        return timeIn*1000


    def get_EstimatedRTT(self):
        ''' get EstimatedRTT '''
        return self._EstimatedRTT
        
        
    def get_DevRTT(self):
        ''' get DevRTT '''
        return self._DevRTT


    def get_timeoutInterval(self):
        ''' get TimeoutInterval '''
        return self._TimeoutInterval


    def calc_timeoutInterval(self):
        ''' calculate TimeoutInterval '''
        timeoutInterval = self.get_EstimatedRTT() + self.get_Gamma() * self.get_DevRTT()
        return timeoutInterval
        

    def calc_EstimatedRTT(self,SampleRTT):
        ''' calculate EstimatedRTT '''
        EstimatedRTT = (1 - defines.ALPHA) * self.get_EstimatedRTT() + defines.ALPHA * SampleRTT
        return EstimatedRTT


    def calc_DevRTT(self,SampleRTT):
        ''' calculate DevRTT '''
        devRTT = (1 - defines.BETA) * self.get_DevRTT() + defines.BETA * abs(SampleRTT - self.get_EstimatedRTT())
        return devRTT


    def update_RTT(self,pane):
        ''' Calculates SampleRTT, and updates EstimatedRTT and DevRTT '''
        if self._RTTStatus is False: return  
        try:
            RTTStart = self.get_TimeoutStart()
            SampleRTT = self.secondToMillisecond(((self.get_Time() - RTTStart).total_seconds()))
            with self._TimerLock:
                ''' Must update in this order as per rfc6298 '''
                self._DevRTT = self.calc_DevRTT(SampleRTT)
                self._EstimatedRTT = self.calc_EstimatedRTT(SampleRTT)
                self._TimeoutInterval = self.calc_timeoutInterval()
                self._RTTStatus = False
        except:
            pass