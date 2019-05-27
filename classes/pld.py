#! /usr/bin/env python3.6

from abc import ABCMeta, abstractmethod
from socket import *
from os import sys, urandom
from classes import defines,arguments,timer,message,window,defines,log
import threading, random
from threading import *

class PLDModule(object):
    ''' PLD Module Object '''
    def __init__(self, stp = None):
        threading.Thread.__init__(self)
        self._Stp = stp
        self.lock = threading.RLock()
        self._reOrderedMsgDelay = 0
        self._reOrderedMsg = None


    def get_Stp(self):
        ''' get PLD STP Object '''
        return self._Stp


    def get_reOrderedMsg(self):
        ''' get PLD ReOrdered Message '''
        return self._reOrderedMsg


    def set_reOrderedMsg(self,msg=None):
        ''' set PLD ReOrdered Message '''
        with self.lock:
            self._reOrderedMsg = msg
            self._reOrderedMsgDelay = self.get_Stp().get_Args().get_maxOrder()


    def send_reOrderedMsg(self):
        ''' send reOrdered msg after maxOrder segments '''
        with self.lock:
            if self._reOrderedMsgDelay == 0:
                msg = self.get_reOrderedMsg()
                if msg is not None:
                    protocol = self.get_Stp()
                    socket = protocol.get_Socket()
                    with protocol.lock:
                        socket.sendto(msg.packMsg(), msg.get_Recipient())
                    self._reOrderedMsg = None
                    protocol.get_LogFile().toFile("snd/rord",protocol.get_TimePassed(),msg.getType(),
                    msg.get_SequenceNumber(),len(msg.get_Payload()),msg.get_ACKNumber())
            else:
                self._reOrderedMsgDelay -= 1
        

    def send(self,msg=None,logEvent="snd"):
        ''' send message via PLD '''
        try:
            if msg is None:
                return
            protocol = self.get_Stp()
            socket = protocol.get_Socket()

            ''' Log File Params '''
            logFile = protocol.get_LogFile()
            logTime = protocol.get_TimePassed()
            logType = msg.getType()
            logSeq = msg.get_SequenceNumber()
            logBytes = len(msg.get_Payload())
            logAck = msg.get_ACKNumber()

            logFile.incr_PLDCount()

            ''' send re-ordered segment '''
            self.send_reOrderedMsg()
            
            if self.dropMsg():
                ''' With probability pDrop, drop the segment '''
                logEvent += "/drop"
                logFile.incr_Dropped()

            elif self.duplicateMsg():
                ''' forward the segment twice back-to-back. '''
                packedMsg = msg.packMsg()
                recipient = msg.get_Recipient()
                with protocol.lock:
                    socket.sendto(packedMsg, recipient)
                    socket.sendto(packedMsg, recipient)
                logEvent += "/dup"
                logFile.incr_Duplicated()
                #logFile.incr_Transmitted() # We transmitted 2x segments??

            elif self.corruptMsg():
                '''introduce one bit error in msg forward the STP segment to UDP '''
                with protocol.lock:
                    socket.sendto(msg.packCorruptedMsg(), msg.get_Recipient())
                logEvent += "/corr"
                logFile.incr_Corrupted()

            elif self.reOrderMsg():
                ''' wait for maxOrder packets before sending segment if no packet waiting reorder. '''
                if self.get_reOrderedMsg() is None:
                    self.set_reOrderedMsg(msg)
                    logFile.incr_ReOrdered()
                    return
                else:
                    with protocol.lock:
                        socket.sendto(msg.packMsg(), msg.get_Recipient())

            elif self.delayMsg():
                ''' Delay segment between 0 to MaxDelay ms '''
                stpDelay = self.getRandomUniform(0,protocol.get_Args().get_maxDelay())
                Timer(stpDelay/1000, sendDelayedMsg,args=[self,msg]).start()
                logFile.incr_Delayed()
                return
            else:
                with protocol.lock:
                    socket.sendto(msg.packMsg(), msg.get_Recipient())

            ''' Log Msg Info '''
            logFile.toFile(logEvent,logTime,logType,logSeq,logBytes,logAck)
            
        except Exception as err:
            log.message.error("send","{}".format(err))


    def getRandom(self):
        ''' return random number between 0 and 1 '''
        randomNum = random.random()
        return randomNum


    def getRandomUniform(self, a, b):
        " return a random number in the range [a -> b]"
        return random.uniform(a, b)


    def dropMsg(self):
        ''' Return True if Dropped Msg Required '''
        args = self.get_Stp().get_Args()
        pDrop = args.get_pDrop()

        randomNumber = self.getRandom()
        if randomNumber < pDrop:
            return True 
        return False


    def duplicateMsg(self):
        ''' Returns True if Duplicated Msg Required '''
        args = self.get_Stp().get_Args()
        pDuplicate = args.get_pDuplicate()

        randomNumber = self.getRandom()
        if randomNumber < pDuplicate:
            return True 
        return False


    def corruptMsg(self):
        ''' Returns True if Corrupted Msg Required '''
        args = self.get_Stp().get_Args()
        pCorrupt = args.get_pCorrupt()

        randomNumber = self.getRandom()
        if randomNumber < pCorrupt:
            return True 
        return False


    def reOrderMsg(self):
        ''' Returns True if ReOrdered Msg Required '''
        args = self.get_Stp().get_Args()
        pOrder = args.get_pOrder()

        randomNumber = self.getRandom()
        if randomNumber < pOrder:
            return True 
        return False

    def delayMsg(self):
        ''' Returns True if Delayed Msg Required '''
        args = self.get_Stp().get_Args()
        pDelay = args.get_pDelay()

        randomNumber = self.getRandom()
        if randomNumber < pDelay:
            return True 
        return False


def sendDelayedMsg(pld,msg):
    ''' Sends a Delayed Message - ignores if connection already terminated'''
    if defines.uploading:
        protocol = pld.get_Stp()
        socket = protocol.get_Socket()
        with protocol.lock:
            socket.sendto(msg.packMsg(), msg.get_Recipient())
        protocol.get_LogFile().toFile("snd/dely",protocol.get_TimePassed(),msg.getType(),
            msg.get_SequenceNumber(),len(msg.get_Payload()),msg.get_ACKNumber())

