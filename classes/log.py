#! /usr/bin/env python3.6

from abc import ABCMeta, abstractmethod
from classes import defines
import threading


SENDER_LOG = "Sender_log"
RECEIVER_LOG = "Receiver_log"

class terminalColours:
    ''' colour defines for msg output '''
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    FAIL = '\033[91m'
    RESET = '\033[0m'


class message():
    def log(colour=terminalColours.RESET,msg=""):
        ''' Print Log Messages to STDOUT '''
        print("{0}{1}{2}".format(colour,msg,terminalColours.RESET))
      
    def error(filename="",msg=""):
        ''' Print Error Log Messages to STDOUT '''
        message.log(terminalColours.FAIL,"Error: ({0}) {1}".format(filename,msg))

    def success(msg="",other=""):
        ''' Print Successful Log Messages to STDOUT '''
        message.log(terminalColours.GREEN,"Success: {}".format(msg))

    def info(msg="",other=""):
        ''' Print Info Log Messages to STDOUT '''
        message.log(terminalColours.BLUE,"Info: {}".format(msg))

    def default(msg="",other=""):
        ''' Print Default Log Messages to STDOUT '''
        message.log(terminalColours.BLUE,"{}".format(msg))


chg = True
def uploadProgress(ackReceived,fileSize,timer):
    global chg
    progress = ackReceived/fileSize
    if chg: 
        prog = "\\"
        chg = False
    else:
        prog = "/"
        chg = True
    print("\rUpload Progress: {0} [{1:25s}] ack: [{2}] timeout: [{3:.2f}] EstRTT: [{4:.2f}]".format(
        prog,'#' * int(progress * 25),ackReceived,timer.get_timeoutInterval(),timer.get_EstimatedRTT()), 
            end="", flush=True)


def downloadProgress(ackReceived):
    global chg
    if chg: 
        prog = "\\"
        chg = False
    else:
        prog = "/"
        chg = True
    print("\rUpload Progress: {0} seq: [{1}]".format(prog,ackReceived), end="", flush=True)




class STPLogs(object):
    ''' Log File Object '''
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def writeResults(self):
        ''' Write Results to File '''
        pass

    @abstractmethod
    def toFile(self,event="",timeRcv = -1.0, typePacket="",seq=-1,numBytes=-1,ack=-1):
        ''' Write RCV/SND Logs to File '''
        print("{0} {1} {2} {3} {4} {5}".format(event,timeRcv,typePacket,seq,numBytes,ack))



class receiverSTPLogs(STPLogs):
    ''' Receiver Log File Object '''
    def __init__(self):
        self.lock = threading.RLock() 
        self._Received  = 0 #Total segments received#
        self._Bytes_Received = 0 #Amount of Data Received (bytes)#
        self._Segments_Received = 0 #Data segments received#
        self._Corrupted_Received = 0 #Data Segments with bit errors#
        self._Duplicate_Received = 0 #Duplicate data segments received#
        self._Duplicate_ACK_Sent = 0 #Duplicate Acks sent#
        ''' Erase Old Log FIle if it exists '''
        f = open(RECEIVER_LOG,defines.WRITE)
        f.close()


    def incr_Received(self):
        ''' Increment STPLog Received by 1 '''
        with self.lock:
            self._Received += 1


    def update_Bytes_Received(self,value:int):
        ''' Increment STPLog Bytes Received by 1 '''
        with self.lock:
            self._Bytes_Received += value


    def incr_Segments_Received(self):
        ''' Increment STPLog Segments Received by 1 '''
        with self.lock:
            self._Segments_Received += 1


    def incr_Corrupted_Received(self):
        ''' Increment STPLog Corrupted Received by 1 '''
        with self.lock:
            self._Corrupted_Received += 1


    def incr_Duplicate_Received(self):
        ''' Increment STPLog Duplicate Received by 1 '''
        with self.lock:
            self._Duplicate_Received += 1


    def incr_Duplicate_ACK_Sent(self):
        ''' Increment STPLog Duplicate ACK Sent by 1 '''
        with self.lock:
            self._Duplicate_ACK_Sent += 1


    def resultsData(self):
            data = '=======================================================\n'
            data += '{:<45} {:>7}\n'.format("Amount of data received (bytes)",self._Bytes_Received)
            data += '{:<45} {:>7}\n'.format('Total Segments Received',self._Received)
            data += '{:<45} {:>7}\n'.format('Data segments received',self._Segments_Received)
            data += '{:<45} {:>7}\n'.format('Data segments with Bit Errors',self._Corrupted_Received)
            data += '{:<45} {:>7}\n'.format('Duplicate data segments received',self._Duplicate_Received)
            data += '{:<45} {:>7}\n'.format('Duplicate ACKs sent',self._Duplicate_ACK_Sent)
            data += '=======================================================\n'
            return data


    def writeResults(self):
        ''' Append Log FIle Results to LogFile '''
        try:
            f = open(RECEIVER_LOG,defines.APPEND)
            results = self.resultsData()
            f.write(results)
            f.close()
            print(results)
        except Exception as err:
            message.error("writeResults","Error Writing LogFile: {}".format(err))


    def toFile(self,event="",timeRcv = -1.0, typePacket="",seq=-1,numBytes=-1,ack=-1):
        ''' Write RCV/SND Logs to File '''
        f = open(RECEIVER_LOG,defines.APPEND)
        #print("{0} {1} {2} {3} {4} {5}".format(event,timeRcv,typePacket,seq,numBytes,ack))
        f.write("{0} {1} {2} {3} {4} {5}\n".format(event,timeRcv,typePacket,seq,numBytes,ack))
        f.close()


class senderSTPLogs(STPLogs):
    ''' Sender Log File Object '''
    def __init__(self):
        self.lock = threading.RLock() 
        self._FileSize = 0 #Size of the file (in Bytes)#
        self._Transmitted = 0 #Segments transmitted (including drop & RXT)#
        self._PLDCount = 0 #Number of Segments handled by PLD#
        self._Dropped = 0 #Number of Segments Dropped#
        self._Corrupted = 0 #Number of Segments Corrupted#
        self._ReOrdered = 0 #Number of Segments Re-ordered#
        self._Duplicated = 0 #Number of Segments Duplicated#
        self._Delayed = 0 #Number of Segments Delayed#
        self._Retransmissions = 0 #Number of Retransmissions due to timeout#
        self._Fast_Retransmissions = 0 #Number of Fast Retransmissions#
        self._Duplicate_ACK_Received = 0 #Number of Duplicate Acknowledgements received#

        f = open(SENDER_LOG,defines.WRITE)
        f.close()


    def set_FileSize(self,value:int):
        ''' Set STPLog FileSize '''
        with self.lock:
            self._FileSize = value


    def get_FileSize(self):
        ''' Get STPLog FileSize '''
        return self._FileSize


    def incr_Transmitted(self):
        ''' Increment STPLog Transmitted by 1 '''
        with self.lock:
            self._Transmitted += 1


    def incr_PLDCount(self):
        ''' Increment STPLog PLD Count by 1 '''
        with self.lock:
            self._PLDCount += 1


    def incr_Dropped(self):
        ''' Increment STPLog Dropped by 1 '''
        with self.lock:
            self._Dropped += 1


    def incr_Corrupted(self):
        ''' Increment STPLog Corrupted by 1 '''
        with self.lock:
            self._Corrupted += 1


    def incr_ReOrdered(self):
        ''' Increment STPLog ReOrdered by 1 '''
        with self.lock:
            self._ReOrdered += 1


    def incr_Duplicated(self):
        ''' Increment STPLog Duplicated by 1 '''
        with self.lock:
            self._Duplicated += 1


    def incr_Delayed(self):
        ''' Increment STPLog Delayed by 1 '''
        with self.lock:
            self._Delayed += 1


    def incr_Retransmissions(self):
        ''' Increment STPLog ReTransmissions by 1 '''
        with self.lock:
            self._Retransmissions += 1


    def incr_Fast_Retransmissions(self):
        ''' Increment STPLog Fast Retransmissions by 1 '''
        with self.lock:
            self._Fast_Retransmissions += 1


    def incr_Duplicate_ACK_Received(self):
        ''' Increment STPLog Duplicate ACK Received by 1 '''
        with self.lock:
            self._Duplicate_ACK_Received += 1   


    def resultsData(self):
            data = '=======================================================\n'
            data += '{:<45} {:>7}\n'.format('Size of the file (in Bytes)',self._FileSize)
            data += '{:<45} {:>7}\n'.format('Segments transmitted (including drop & RXT)',self._Transmitted)
            data += '{:<45} {:>7}\n'.format('Number of Segments handled by PLD',self._PLDCount)
            data += '{:<45} {:>7}\n'.format('Number of Segments dropped',self._Dropped)
            data += '{:<45} {:>7}\n'.format('Number of Segments Corrupted',self._Corrupted)
            data += '{:<45} {:>7}\n'.format('Number of Segments Re-ordered',self._ReOrdered)
            data += '{:<45} {:>7}\n'.format('Number of Segments Duplicated',self._Duplicated)
            data += '{:<45} {:>7}\n'.format('Number of Segments Delayed',self._Delayed)
            data += '{:<45} {:>7}\n'.format('Number of Retransmissions due to TIMEOUT',self._Retransmissions)
            data += '{:<45} {:>7}\n'.format('Number of FAST RETRANSMISSION',self._Fast_Retransmissions)
            data += '{:<45} {:>7}\n'.format('Number of DUP ACKS received',self._Duplicate_ACK_Received)
            data += '=======================================================\n'
            return data

    def writeResults(self):
        ''' Append Log FIle Results to LogFile '''
        try:
            f = open(SENDER_LOG,defines.APPEND)
            results = self.resultsData()
            f.write(results)
            f.close()
            print(results)
        except Exception as err:
            message.error("writeResults","Error Writing LogFile: {}".format(err))


    def toFile(self,event="",timeRcv = -1.0, typePacket="",seq=-1,numBytes=-1,ack=-1):
        ''' Write RCV/SND Logs to File '''
        f = open(SENDER_LOG,defines.APPEND)
        #print("{0} {1} {2} {3} {4} {5}".format(event,timeRcv,typePacket,seq,numBytes,ack))
        f.write("{0} {1} {2} {3} {4} {5}\n".format(event,timeRcv,typePacket,seq,numBytes,ack))
        f.close()