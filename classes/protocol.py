#! /usr/bin/env python3.6

from abc import ABCMeta, abstractmethod
from socket import *
from os import sys, urandom
from heapq import *
from classes import defines,arguments,timer,message,window,pld,defines,log
from enum import IntFlag, auto
from math import floor
import threading, datetime


class STPConnection(object):
    ''' Make an STP connection object '''

    @abstractmethod
    def __init__(self):
        ''' Initialises an STP Message Object '''
        self._Socket = None
        self._Args = None
        self.lock = threading.RLock() 
        self._time = datetime.datetime.now()
        self._logFile = None


    @abstractmethod
    def connect(self):
        ''' initiate STPConnection '''
        pass


    @abstractmethod
    def handShake(self):
        ''' complete a connection handshake sequence '''
        pass


    @abstractmethod
    def sendMsg(self,msg):
        ''' Sends Message to its stored sender '''
        pass


    @abstractmethod
    def set_Args(self,args):
        ''' set STP Arguments '''
        self._Args = args


    @abstractmethod
    def listen(self):
        ''' listen for a packet and return msg object'''
        pass


    def get_LogFile(self):
        ''' return STP Log Object '''
        return self._logFile


    def get_Socket(self):
        ''' return STP Socket Object '''
        return self._Socket


    def get_Args(self):
        ''' return STP Argument Object '''
        return self._Args


    def get_Time(self):
        ''' return STP Start Time '''
        return self._time


    def get_TimePassed(self):
        ''' calculate time expired since STP Start Time '''
        timePassed = (datetime.datetime.now() - self.get_Time()).total_seconds()
        return round(timePassed,2)


    def sendSYN(self,msg):
        ''' Send a SYN request '''
        msg.set_SYN(True)
        self.sendMsg(msg,False)


    def sendACK(self,msg,event="snd"):
        ''' Send a ACK request '''
        msg.set_ACK(True)
        self.sendMsg(msg,False,event)


    def sendSYNACK(self,msg):
        ''' Send a SYNACK request '''
        msg.set_SYNACK(True)
        self.sendMsg(msg,False)


    def sendFIN(self,msg):
        ''' Send a FIN request '''
        msg.set_FIN(True)
        msg.set_Payload("")
        self.sendMsg(msg,False)


    def is_FIN(self):
        ''' return True if FIN flag set '''
        return ((self.get_Flags() & defines.Perm.FIN) is defines.Perm.FIN)


    def is_SYN(self):
        ''' return True if SYN flag set '''
        return ((self.get_Flags() & defines.Perm.SYN) is defines.Perm.SYN)


    def is_ACK(self):
        ''' return True if ACK flag set '''
        return ((self.get_Flags() & defines.Perm.ACK) is defines.Perm.ACK)


    def is_SYNACK(self):
        ''' return True if SYN/ACK flag set '''
        return ((self.get_Flags() & defines.Perm.SYNACK) is defines.Perm.SYNACK)




class STPSender(STPConnection):
    ''' Sender Client '''
    def __init__(self):
        ''' Initialises an STP Message Object '''
        self._Socket = None
        self._Args = None
        self._SequenceNumber = 0 #this holds the next sequence number we will send
        self._AckNumber = 0 #acknum does not change as this is a one way connection
        self._MsgWindow = window.STPWindow() # Window Frame of Messages
        self._Timer = timer.STDTimer() # Timer, EstimatedRTT etc
        self._PLD = None
        self.lock = threading.RLock()        
        self._time = datetime.datetime.now()
        self._logFile = log.senderSTPLogs()
        

    def get_Timer(self):
        ''' return STP Timer Object '''
        return self._Timer


    def get_SequenceNumber(self):
        ''' return STP Sequence Number '''
        return self._SequenceNumber


    def set_SequenceNumber(self,value:int):
        ''' set STP Sequence Number '''
        self._SequenceNumber = value
        return value


    def set_AckNumber(self,value:int):
        ''' set STP ACK Number '''
        self._AckNumber = value
        return value


    def get_AckNumber(self):
        ''' get STP ACK Number '''
        return self._AckNumber


    def set_Args(self,args):
        ''' set STP Arguments Object '''
        self._Args = args
        timer = self.get_Timer()
        timer.set_Gamma(args.get_gamma())


    def set_MsgWindow(self,window:object):
        ''' set STP Msg Window object '''
        self._MsgWindow = window


    def get_MsgWindow(self):
        ''' get STP Msg Window Object '''
        return self._MsgWindow


    def init_PLD(self):
        ''' create and set STP PLD Object '''
        self._PLD = pld.PLDModule(self)


    def get_PLD(self):
        ''' get STP PLD Object '''
        return self._PLD


    def connect(self):
        ''' initiates STPConnection and carries out handshake '''
        if self._Socket is not None:
            log.message.error("STPConnection","Connection already active!")
            sys.exit()
        with self.lock:
            self._Socket = socket(AF_INET, defines.UDPSOCKET)
            self.handShake()


    def sendMsgWindow(self):
        ''' Sends any new unsent messages from our window '''
        try:
            window = self.get_MsgWindow()
            timer = self.get_Timer()
            minPane = window.get_minPane()
            maxPane = window.get_maxPane()
            args = self.get_Args()
            receiver = args.get_receiver()   

            msgQueue = window.get_msgQueue()
            if msgQueue is None:
                log.message.error("sendMsgWindow","No Msg Queue Created")
                sys.exit()

            ''' Send any unsent msgs '''
            for pane in range(minPane,maxPane+1):
                msgTuple = msgQueue.get_msg(pane)
                if len(msgTuple) == 3:
                    payload, payloadSeq, payloadAck = msgTuple
                    if window.msg_sent(payloadAck) is False:
                        msg = message.build(receiver,payload,payloadSeq,self.get_AckNumber())           
                        self.sendMsg(msg)
                        timer = self.get_Timer()
                        if timer.TimeoutStarted() is False or timer.TimeoutExpired():
                            timer.startTimeoutTimer(True)

                        window.set_window_status(payloadAck,defines.Status.SENT)
        except Exception as err:
            log.message.error("sendMsgWindow","{}".format(err))


    def sendMsg(self,msg=None,pldEnabled=True,event="snd"):
        ''' Sends Message to its receiver - PLD Enabled by default '''
        try:
            connection = self.get_Socket()
            logFile = self.get_LogFile()
            logFile.incr_Transmitted()
            logTime = self.get_TimePassed()
            if pldEnabled:
                ''' PLD Module Determines Msg Events '''
                self.get_PLD().send(msg,logEvent=event)
            else:
                ''' Handshake/Terminate '''
                with self.lock:
                    connection.sendto(msg.packMsg(), msg.get_Recipient())
                logFile.toFile(event,logTime,msg.getType(),msg.get_SequenceNumber(),len(msg.get_Payload()),msg.get_ACKNumber())
        except Exception as err:
            log.message.error("sendMsg","{}".format(err))


    def init_msg_queue(self):
        ''' open file and break into segments'''
        try:
            msgQueue = []
            args = self.get_Args()
            with open(args.get_filename(),defines.READ_BYTE) as f:
                readLength = args.get_max_segment_size()      

                ''' store each msg payload into our msg queue with its sequence and expected ack number '''
                seqNum = self.get_SequenceNumber()
                msgQueue = message.STPMSGQueue()

                while True:
                    msg = f.read(readLength)
                    if msg:
                        msgLen = len(msg)
                        ackNum = seqNum+msgLen
                        msgQueue.add((msg,seqNum,ackNum))
                        seqNum += msgLen
                    else:
                        break

            ''' store the msgQueue onto our sockets window '''
            self.get_MsgWindow().set_msgQueue(msgQueue)
            self.get_LogFile().set_FileSize(max(0,seqNum-1))
            
        except Exception as err:
            log.message.error("build_msg_queue","{}".format(err))
            sys.exit()


    def init_window_frame(self):
        ''' Initialise window frame '''
        try:
            args = self.get_Args()

            ''' Calculate the max number of window panes in our sliding window (MIN 1) '''
            numWindowPanes = max(floor(args.get_max_window_size() / args.get_max_segment_size()),1)
            assert(numWindowPanes*args.get_max_segment_size() <= args.get_max_window_size()),"Invalid Window Size"

            window = self.get_MsgWindow()
            window.set_numWindowPanes(numWindowPanes)
            window.set_maxPane(numWindowPanes-1)
        except Exception as err:
            log.message.error("init_window_frame","{}".format(err))


    def update_window(self,msg):
        ''' Updates the message window frame and RTT Timers '''
        try:
            ackNum = msg.get_ACKNumber()
            logFile = self.get_LogFile()
            logTime = self.get_TimePassed()

            window = self.get_MsgWindow()
            minPane = window.get_minPane()
            maxPane = window.get_maxPane()
            numWindowPanes = window.get_numWindowPanes()
            msgQueue = window.get_msgQueue()
            queueLength = msgQueue.get_length()
            
            ackStatus = window.set_window_status(ackNum,window.get_window_status(ackNum)+1)

            recvPane = msgQueue.get_key_index(ackNum)   
            if recvPane == -1:
                logFile.toFile("rcv",logTime,msg.getType(),msg.get_SequenceNumber(),len(msg.get_Payload()),msg.get_ACKNumber())
                return True        

            log.uploadProgress(ackNum,logFile.get_FileSize(),self.get_Timer())

            ''' slide the message window along queue '''
            if recvPane >= minPane:
                logFile.toFile("rcv",logTime,msg.getType(),msg.get_SequenceNumber(),len(msg.get_Payload()),msg.get_ACKNumber())

                ''' Update Timers '''
                timer = self.get_Timer()
                timer.update_RTT(recvPane)

                ''' Update Window '''
                window.set_window_status(ackNum,defines.Status.RECEIVED)
                self.set_SequenceNumber(ackNum)
                minPane = window.set_minPane(recvPane+1)

                ''' finished uploading file '''
                if minPane == queueLength:
                    return False

                ''' Restart the Timer if UnACK'd Msgs from old window remaining (No RTTEst) '''
                if minPane <= maxPane:
                    self.get_Timer().startTimeoutTimer()

                ''' update maxPane -> cannot exceed queueLength'''
                maxPane = window.set_maxPane(min((minPane + (numWindowPanes-1)),queueLength))

            else:
                ''' Increment number of duplicate ACKS's for this pane '''
                logFile.incr_Duplicate_ACK_Received()
                logFile.toFile("rcv/DA",logTime,msg.getType(),msg.get_SequenceNumber(),len(msg.get_Payload()),msg.get_ACKNumber())

                ''' If 3 ACK's Received, resend msg '''
                if ackStatus == defines.Status.RECEIVED_3:
                    receiver = self.get_Args().get_receiver()
                    msg = msgQueue.get_msg(recvPane+1)
                    if len(msg) == 3:
                        ''' Build and Re-Send the msg to the server '''  
                        payload, payloadSeq, payloadAck = msg
                        msg = message.build(receiver,payload,payloadSeq,self.get_AckNumber())             
                        self.sendMsg(msg,event="snd/RXT")
                        logFile.incr_Fast_Retransmissions()

                        ''' Restart the Timer (No RTTEst)'''
                        timer = self.get_Timer()
                        timer.startTimeoutTimer() 

                        ''' Restart Ack Count '''
                        window.set_window_status(ackNum,defines.Status.SENT)

                        
        except Exception as err:
            log.message.error("update_window","{}".format(err))
        return True


    def handShake(self):
        ''' Initiate Handshake With Receiver Connection '''
        log.message.info("Handshake Initiated")
        try:
            ''' Init Sequence Number with Random number '''
            msg = message.STPMessage()
            msg.set_Recipient(self.get_Args().get_receiver())          
            seqNum = self.get_SequenceNumber()
            msg.set_ACKNumber(0)
            msg.set_SequenceNumber(seqNum) 

            logFile = self.get_LogFile()

            ''' store next sequence number we expect from the server '''
            seqNum = self.set_SequenceNumber(seqNum+1)
            
            ''' Send and wait for SYN ACK Response '''
            self.sendSYN(msg)
            while True:
                msg = self.listen()
                if msg is not None and msg.is_SYNACK() and msg.get_ACKNumber() == seqNum:
                    logFile.toFile("rcv",self.get_TimePassed(),msg.getType(),msg.get_SequenceNumber(),len(msg.get_Payload()),msg.get_ACKNumber())
                    break
                else:
                    log.message.error("handShake","Invalid Message received! Expected: {} Received: {}".format(seqNum,msg.get_ACKNumber()))

            ''' Send ACK Response '''
            ackMSG = msg.createACKResponse(1)
            self.sendACK(ackMSG)

            log.message.success("Connection Established")
            self.set_AckNumber(ackMSG.get_ACKNumber())

            ''' disable blocking on the socket '''
            self.get_Socket().setblocking(0)
            print("")

        except Exception as err:
            log.message.error("handShake","{}".format(err))


    def tearDown(self):
        ''' Complete Connection Teardown '''
        log.message.info("TearDown Initiated")
        try:
            ''' re-enable blocking on the socket '''
            self.get_Socket().setblocking(1)

            ''' Update SEQ/ACK Numbers '''
            msg = message.STPMessage()
            msg.set_Recipient(self.get_Args().get_receiver())
            msg.set_ACKNumber(self.get_AckNumber())
            seqNum = self.get_SequenceNumber()
            msg.set_SequenceNumber(seqNum) 
            seqNum = self.set_SequenceNumber(seqNum+1)
            logFile = self.get_LogFile()
            
            ''' Send FIN MSG '''
            msg.resetFlag()
            self.sendFIN(msg)

            ''' FIN_WAIT_1 '''
            while True:
                msg = self.listen()
                rcvAck = msg.get_ACKNumber()
                if msg is not None:
                    if msg.is_ACK():
                        if rcvAck == seqNum:
                            logFile.toFile("rcv",self.get_TimePassed(),msg.getType(),msg.get_SequenceNumber(),len(msg.get_Payload()),msg.get_ACKNumber())
                            break
                        elif rcvAck < seqNum:
                            ''' Drop Old Delayed ACK from File Transfer '''
                            continue
                log.message.error("tearDown","Invalid ACK received!")
                sys.exit()

            ''' FIN_WAIT_2 '''
            while True:
                msg = self.listen()
                rcvAck = msg.get_ACKNumber()
                if msg is not None:
                    if msg.is_ACK() and rcvAck < seqNum:
                        ''' Old Delayed ACK from File Transfer '''
                        continue
                    if msg.is_FIN():
                        logFile.toFile("rcv",self.get_TimePassed(),msg.getType(),msg.get_SequenceNumber(),len(msg.get_Payload()),msg.get_ACKNumber())
                        break
                log.message.error("tearDown","Invalid FIN received!")
                sys.exit()

            ''' Update SEQ/ACK Numbers '''
            msg.set_ACKNumber(msg.get_SequenceNumber()+1)
            msg.set_SequenceNumber(seqNum) 
            seqNum = self.set_SequenceNumber(seqNum+1)
    
            ''' Send ACK Response '''
            msg.resetFlag()
            self.sendACK(msg)

            logFile = self.get_LogFile()
            logFile.writeResults()

            log.message.success("Connection Terminated")

        except Exception as err:
            log.message.error("tearDown","{}".format(err))


    def listen(self):
        ''' listen for a packet and return msg object'''
        socket = self.get_Socket()
        try:
            with self.lock:
                packet,sender = socket.recvfrom(defines.BUFFER_SIZE)
            
            msg = message.STPMessage()
            if msg is None: return None

            unPacked = msg.unpackMsg(packet)
            if unPacked != defines.SUCCESS:
                return None 
            msg.set_Recipient(sender)
            return msg
        except KeyboardInterrupt:
            sys.exit()
        except:
            return None




class STPReceiver(STPConnection):
    ''' Receiver Server '''
    def __init__(self):
        ''' Initialises an STP Message Object '''
        self._Socket = None
        self.lock = threading.RLock()
        self._Receiver = None
        self._Connections = {} # dictionary of connections permits simultaneous uploads
        self._Args = None
        self._time = datetime.datetime.now()
        self._logFile = log.receiverSTPLogs()


    def set_Receiver(self,receiver):
        ''' Store the IP/PORT our server is using '''
        self._Receiver = receiver


    def set_ConnectionSender(self,sender):
        ''' set a senders connection sender '''
        self._Connections[sender]['sender'] = sender


    def set_ConnectionSeq(self,sender,seq):
        ''' set a senders connection SEQ '''
        self._Connections[sender]['seq'] = seq


    def set_ConnectionACK(self,sender,ack):
        ''' set a senders connection ACK '''
        self._Connections[sender]['ack'] = ack


    def get_ConnectionSeq(self,sender):
        ''' return a senders connection SEQ '''
        connection = self.get_Connection(sender)
        if connection is None:
            return -1
        return connection['seq']


    def get_ConnectionACK(self,sender):
        ''' return a senders connection ACK '''
        connection = self.get_Connection(sender)
        if connection is None:
            return -1
        return connection['ack']
    

    def get_Connection(self,sender:tuple):
        ''' return a senders connection object '''
        try:
            connection = self._Connections[sender]
        except:
            connection = None
        return connection
   

    def get_CumulativeACK(self,sender,nextAck):
        ''' Calculates the Cumulative ACK we next expect from sender '''
        try:
            connection = self.get_Connection(sender)
            if connection is None:
                log.message.error("get_CumulativeACK","Connection does not exist!")
                return

            buffer = connection['buffer']
            listLen = len(buffer)
   
            if listLen < 1: return nextAck
            for seq, msg in buffer:
                if seq < nextAck:
                    continue
                if seq != nextAck:
                    break
                nextAck = seq + len(msg)

            return nextAck

        except Exception as error:
            log.message.error("get_CumulativeACK","Error: {}".format(error))


    def add_ConnectionBuffer(self,msg):
        ''' Store message into connections message buffer '''
        sender = msg.get_Recipient()
        sequence = msg.get_SequenceNumber()
        payload = msg.get_Payload()
        try:
            connection = self.get_Connection(sender)
            if connection is None:
                log.message.error("add_ConnectionBuffer","Connection does not exist!\n\n --- DUMPING MSG CONTENTS ---")
                return False
            newMsg = (sequence,payload)
            if newMsg not in connection['buffer']:
                ''' only buffer messages we have not received already '''
                connection['buffer'].append((sequence,payload))
                connection['buffer'] = sorted(connection['buffer'])
                return True
            else:
                return False
        except Exception as error:
            log.message.error("add_ConnectionBuffer","Error: {}\n\n --- DUMPING MSG CONTENTS ---".format(error))
            return False


    def assemble_msg(self,sender):
        ''' Assembles a transferred file from all the received connection messages '''
        msg = b''
        connection = self.get_Connection(sender)
        if connection is None:
            log.message.error("assemble_msg","Connection does not exist!")
            return msg
        while(1):
            try:
                item = heappop(connection['buffer'])
                if item is None:
                    break
                msg = b''.join([msg, item[1]])
            except:
                break
        return msg


    def add_Connection(self,sender:tuple,seq=0,ack=0):
        ''' Adds a new client connection and returns object '''
        connection = self.get_Connection(sender)
        if connection is None:
            self._Connections[sender] = {}
            self._Connections[sender]['sender'] = sender
            self._Connections[sender]['seq'] = seq
            self._Connections[sender]['ack'] = ack
            self._Connections[sender]['buffer'] = [] # Min Heap
            connection = self._Connections[sender]
        return connection


    def remove_Connection(self,sender:tuple):
        ''' Removes a client connection '''
        connection = self.get_Connection(sender)
        if connection is not None:
            del self._Connections[sender]
        connection = self.get_Connection(sender)
        if connection is not None:
            log.message.error("remove_Connection","Error Removing Connection!")


    def connect(self):
        ''' Creates a Listening STPConnection '''
        if self._Socket is not None:
            log.message.error("STPConnection","Listening Server Already Initialised!")
            sys.exit()

        self._Socket = socket(AF_INET, defines.UDPSOCKET)
        self._Socket.bind(self._Receiver)


    def sendMsg(self,msg=None,pldEnabled=False,event="snd"):
        ''' Sends Message to its receiver '''       
        try:
            socket = self.get_Socket()
            logFile = self.get_LogFile()
            logTime = self.get_TimePassed()
            socket.sendto(msg.packMsg(), msg.get_Recipient())
            logFile.toFile(event,logTime,msg.getType(),msg.get_SequenceNumber(),len(msg.get_Payload()),msg.get_ACKNumber())
        except:
            log.message.error("sendMsg","Error Sending Message!")

 
    def handShake(self,msg):
        ''' Complete a new connection handshake request '''
        if msg.is_SYN():
            log.message.info("Initiating Handshake")

            ''' Init Sequence Number with Random number and increment ACK number'''
            #seqNum = int.from_bytes(urandom(4), sys.byteorder)
            storedSeqNum = 0
            rcvAckNum = msg.get_SequenceNumber()+1

            ''' Store new connection - Note vulnerable to SYN flooding! '''
            try:
                sender = msg.get_Recipient()
                ''' Send SYN-ACK Response '''
                msg.set_ACKNumber(rcvAckNum)
                msg.set_SequenceNumber(storedSeqNum) 
                self.sendSYNACK(msg)

                ''' Store incremented Seq and Ack Numbers'''
                self.add_Connection(sender,storedSeqNum + 1,rcvAckNum)

            except:
                log.message.error("handShake","Error Initiating Handshake!")
        else:
            log.message.error("handShake","Error Receiving Handshake!")
    

    def tearDown(self,msg):
        ''' Complete Connection Teardown '''
        log.message.info("TearDown Requested")
        try:
            ''' Update SEQ/ACK Numbers '''
            msg.set_ACKNumber(msg.get_SequenceNumber()+1)
            connection = self.get_Connection(msg.get_Recipient())
            seqNum = connection['seq']
            msg.set_SequenceNumber(connection['seq']) 
            seqNum += 1
            connection['seq'] = seqNum

            ''' Send ACK MSG '''
            msg.resetFlag()
            self.sendACK(msg)

            ''' Send FIN MSG '''
            msg.resetFlag()
            self.sendFIN(msg)

            ''' Wait for ACK Response - LAST_ACK '''
            while True:
                msg = self.listen()
                if msg is not None and msg.is_ACK() and msg.get_ACKNumber() == seqNum:
                    break
                else:
                    ''' Old Delayed MSG from File Transfer '''
                    continue

            ''' Build and Store Transferred File'''
            data = self.assemble_msg(msg.get_Recipient())
            self.remove_Connection(msg.get_Recipient())

            logFile = self.get_LogFile()
            logFile.writeResults()
            try:
                args = self.get_Args()
                f = open(args.get_filename(),defines.WRITE_BYTE)
                f.write(data)
                f.close()
                
            except Exception as err:
                log.message.error("tearDown","Error Writing File: {}".format(err))
            log.message.success("Connection Terminated")
        except Exception as err:
            log.message.error("tearDown","{}".format(err))


    def listen(self):
        ''' listen for a packet and return msg object'''
        socket = self.get_Socket()
        try:
            with self.lock:
                packet,sender = socket.recvfrom(defines.BUFFER_SIZE)
            
            msg = message.STPMessage()
            if msg is None: return None

            logFile = self.get_LogFile()
            logTime = self.get_TimePassed()

            unPacked = msg.unpackMsg(packet)
            if unPacked != defines.SUCCESS:
                logFile.incr_Corrupted_Received()
                return None               

            msg.set_Recipient(sender)
            dataLen = len(msg.get_Payload())
            if(dataLen > 0):
                logFile.incr_Segments_Received()
                logFile.update_Bytes_Received(dataLen)         

            logFile.incr_Received()
            logFile.toFile("rcv",logTime,msg.getType(),msg.get_SequenceNumber(),len(msg.get_Payload()),msg.get_ACKNumber())
            return msg
        except KeyboardInterrupt:
            sys.exit()
        except:
            return None