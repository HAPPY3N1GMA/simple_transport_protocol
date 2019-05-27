#! /usr/bin/env python3.6

from os import sys
import struct, binascii, hashlib
from classes import defines,protocol,threads,arguments,timer,log


class STPMessage(object):
    ''' STP Message Type Object '''
    def __init__(self):
        self._SequenceNumber = 0
        self._ACKNumber = 0
        self._Flags = defines.Perm.DEFAULT
        self._Payload = ""
        self._Recipient = None
        

    def set_SequenceNumber(self,value: int):
        ''' set STPMessage Seq Number '''
        self._SequenceNumber = value


    def get_SequenceNumber(self):
        ''' get STPMessage Seq Number '''
        return self._SequenceNumber


    def set_ACKNumber(self,value: int):
        ''' set STPMessage ACK Number '''
        self._ACKNumber = value


    def get_ACKNumber(self):
        ''' get STPMessage ACK Number '''
        return self._ACKNumber


    def resetFlag(self):
        ''' reset STPMessage Flag to 0 '''
        self._Flags = defines.Perm.DEFAULT


    def get_Flags(self):
        ''' get STPMessage Flag '''
        return self._Flags


    def set_CheckSum(self,value: int):
        ''' set STPMessage CheckSum '''
        self._CheckSum = value


    def get_CheckSum(self):
        ''' get STPMessage CheckSum '''
        return self._CheckSum


    def set_Payload(self,value):
        ''' set STPMessage Payload '''
        self._Payload = value


    def get_Payload(self):
        ''' get STPMessage Payload '''
        return self._Payload


    def set_Recipient(self,recipient):
        ''' set STPMessage Recipient '''
        if len(recipient) != 2:
            log.message.error("set_Recipient","Invalid Recipient!")
            sys.exit()
        self._Recipient = recipient


    def get_Recipient(self):
        ''' get STPMessage Recipient '''
        return self._Recipient


    def set_ACK(self,value: bool):
        ''' set STPMessage ACK Flag '''
        if value: 
            self._Flags |= defines.Perm.ACK
        else:
            self._Flags &= ~defines.Perm.ACK
        

    def set_SYN(self,value: bool):
        ''' set STPMessage SYN Flag '''
        if value: 
            self._Flags |= defines.Perm.SYN
        else:
            self._Flags &= ~defines.Perm.SYN
        

    def set_SYNACK(self,value: bool):
        ''' set STPMessage SYN/ACK Flag '''
        if value: 
            self._Flags |= defines.Perm.SYNACK
        else:
            self._Flags &= ~defines.Perm.SYNACK
        

    def set_FIN(self,value: bool):
        ''' set STPMessage FIN Flag '''
        if value: 
            self._Flags = defines.Perm.FIN
        else:
            self._Flags &= ~defines.Perm.FIN


    def is_FIN(self):
        ''' get STPMessage FIN Flag '''
        return ((self.get_Flags() & defines.Perm.FIN) is defines.Perm.FIN)


    def is_SYN(self):
        ''' get STPMessage SYN Flag '''
        return ((self.get_Flags() & defines.Perm.SYN) is defines.Perm.SYN)


    def is_ACK(self):
        return ((self.get_Flags() & defines.Perm.ACK) is defines.Perm.ACK)


    def is_SYNACK(self):
        ''' get STPMessage SYN/ACK Flag '''
        return ((self.get_Flags() & defines.Perm.SYNACK) is defines.Perm.SYNACK)


    def is_DATA(self):
        ''' return True if msg contains a payload '''
        return (len(self.get_Payload()) > 0)


    def getType(self):
        ''' return STPMessage Flag Codes '''
        if self.is_SYNACK(): return "SA"
        if self.is_DATA(): return "D"
        if self.is_FIN(): return "F"
        if self.is_SYN(): return "S"
        if self.is_ACK(): return "A"


    def isCorrupted(self,chk):
        ''' return True if STPMessage Checksum Fails '''
        return chk != self.calc_CheckSum(self.packMsgNoHash())


    def createACKResponse(self,msgLength = 0):
        ''' Swap the Message Ack/Seq Fields and increment ACK '''
        seq = self.get_ACKNumber()
        ack = self.get_SequenceNumber() + msgLength
        sender = self.get_Recipient()

        msg = STPMessage()
        msg.set_Recipient(sender)
        msg.set_ACKNumber(ack)
        msg.set_SequenceNumber(seq) 

        return msg


    def checksum(self,msg):
        ''' 
            Calculate a 16 bit hash of msg 
            as per RFC https://tools.ietf.org/html/rfc1071 
        '''
        msgSum = 0
        if len(msg)%2:
            msg += "\x00".encode('utf-8')
        for (a, b) in zip(msg[0::2], msg[1::2]):
            curr = msgSum + (a + (b << 8))
            msgSum = (curr & 0xffff) + (curr >> 16)
        return ~msgSum & 0xffff


    def calc_CheckSum(self,msg):
        ''' Calculate the Checksum of msg '''
        hashValue = self.checksum(msg)
        return (hashValue).to_bytes(2, 'little')


    def packMsg(self):
        ''' Packs message into STPMessage Packet (big endian) with checksum hash '''
        msg = struct.pack("!LLB",self._SequenceNumber,self._ACKNumber,self._Flags)
        msg += self.calc_CheckSum(self.packMsgNoHash())
        if type(self._Payload) is str:
            msg += self._Payload.encode('utf-8')
        else:
            msg += self._Payload
        return msg


    def packMsgNoHash(self):
        ''' Packs message into STPMessage Packet (big endian) with no checksum hash '''
        msg = struct.pack("!LLB", self._SequenceNumber, self._ACKNumber, self._Flags)
        msg += "\x00\x00".encode('utf-8')
        if type(self._Payload) is str:
            msg += self._Payload.encode('utf-8')
        else:
            msg += self._Payload
        return msg


    def packCorruptedMsg(self):
        ''' Packs a corrupted message (flag has single bit error) into STPMessage Packet (big endian) '''
        msg = struct.pack("!LLB", self._SequenceNumber, self._ACKNumber, self._Flags + 1)
        msg += self.calc_CheckSum(self.packMsgNoHash())
        if type(self._Payload) is str:
            msg += self._Payload.encode('utf-8')
        else:
            msg += self._Payload
        return msg


    def unpackMsg(self,msg):
        ''' unpacks message STPMessage'''
        try:
            self._SequenceNumber, self._ACKNumber, self._Flags, CheckSum = struct.unpack("!LLB2s",msg[:11])
            self._Payload = msg[11:]

            ''' check the checksum matches '''
            if self.isCorrupted(CheckSum):
                return defines.CORRUPT

        except Exception as err:
            log.message.error("unpackMsg","{}".format(err))
            return defines.FAILURE
        return defines.SUCCESS


    def debugMsg(self):
        ''' Prints out entire contents of a message object '''
        print("-------------------------------------")
        print("Recipient: {}".format(self._Recipient))
        print("Sequence: {}".format(self._SequenceNumber))
        print("Len: {}".format(len(self._Payload)))
        print("ACK: {}".format(self._ACKNumber))
        print("Flags: {}".format(self._Flags))
        print("Payload: {}".format(self._Payload))
        print("-------------------------------------")


class STPMSGQueue(object):
    ''' STP message queue '''
    def __init__(self):
        self._msgQueue = []
        self._length = 0


    def add(self,item:tuple):
        ''' add items to msg queue - (msg,seqNum,ackNum) '''
        try:
            if item not in self._msgQueue:
                self._msgQueue.append(item)
                self._length += 1
        except:
            pass


    def remove(self,index:int):
        ''' remove items from msg queue '''
        try:
            self._msgQueue.remove(index)
            self._length -= 1
        except:
            pass


    def get_msgQueue(self):
        ''' returns the Msg Queue '''
        return self._msgQueue


    def get_msg(self,index):
        ''' returns msg tuple from index '''
        if index >= 0 and index < self._length:
            return self.get_msgQueue()[index]
        return ()


    def get_key(self,index):
        ''' return a queue index's tuple '''
        msg = self.get_msg(index)
        if len(msg) != 3:
            return -1
        return msg[2]


    def get_key_index(self,key):
        ''' returns a keys queue index '''
        for i in range(0,self.get_length()):
            if self.get_key(i) == key:
                return i
        return -1


    def get_length(self):
        ''' return the queue length '''
        return self._length



def build(receiver,payload,seq,ack):
    ''' Build Msg Object '''
    try:
        msg = STPMessage()
        msg.set_Recipient(receiver)
        msg.set_Payload(payload)

        msg.set_ACKNumber(ack)
        msg.set_SequenceNumber(seq)
        return msg

    except:
        log.message.error("build","Error building MSG!")
        return None
