#! /usr/bin/env python3.6

import threading, time, signal
from classes import defines,protocol,window,message,timer,log


class ServiceExit(Exception):
    """
    Exception to trigger the clean exit
    of all running threads and the main program.
    """
    pass

def terminate_thread(signum, frame):
    ''' Signal Event to Terminate Sender Thread '''
    ''' https://www.g-loaded.eu/2016/11/24/how-to-terminate-running-python-threads-using-signals/ '''
    log.message.error("terminate_thread","File Transfer Failed")
    raise ServiceExit


class senderThread(threading.Thread):
    ''' Sender Thread Object '''
    def __init__(self, socket = None):
        threading.Thread.__init__(self)
        self._socket = socket
        self.shutdown_flag = threading.Event()
    

    def get_Socket(self):
        ''' get socket object '''
        return self._socket


    def run(self):
        ''' run sender thread '''
        socket = self.get_Socket()
        window = socket.get_MsgWindow()
        msgQueue = window.get_msgQueue()
        logFile = socket.get_LogFile()
        
        while not self.shutdown_flag.is_set():
            ''' Timeout Event - Restransmit MinPane '''
            timer = socket.get_Timer()
            if timer.TimeoutExpired():
                minPane = window.get_minPane()
                payload, payloadSeq, payloadAck = msgQueue.get_msg(minPane)

                ''' ReSend the msg to the server '''    
                receiver = socket.get_Args().get_receiver()   
                msg = message.build(receiver,payload,payloadSeq,socket.get_AckNumber())  
                socket.sendMsg(msg,event="snd/RXT")

                ''' Restart Timer (No RTTEst) '''
                timer.startTimeoutTimer()
                logFile.incr_Retransmissions()

            ''' Send any New Messages '''
            socket.sendMsgWindow()
