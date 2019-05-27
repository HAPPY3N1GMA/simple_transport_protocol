#! /usr/bin/env python3.6

import sys,time,datetime,string
from classes import arguments,protocol,message,defines,log
from os import sys
from socket import *


def main(args):
    ''' initialise STP protocol '''
    socket = protocol.STPReceiver()
    socket.set_Receiver(args.get_receiver()) 
    socket.set_Args(args)
    socket.connect()
    log.message.info("Awaiting Connection")
    logFile = socket.get_LogFile()

    while True:
        try:
            msg = socket.listen()
            if msg is not None:
                sender = msg.get_Recipient()
                ''' Initiate New Connection '''
                if socket.get_Connection(sender) is None:
                    socket.handShake(msg)
                else:
                    ''' Receive next Packet '''
                    msgLength = len(msg.get_Payload())
                    if msgLength > 0:

                        rcvSeqNum = msg.get_SequenceNumber()
                        rcvAckNum = msg.get_ACKNumber()
                        expectedAckNum = socket.get_ConnectionSeq(sender)
                        expectedSeqNum = socket.get_ConnectionACK(sender)
                        event = "snd"

                        log.downloadProgress(rcvSeqNum)

                        ''' check the ACK matches my stored Sequence Number '''
                        if rcvAckNum != expectedAckNum:
                            log.message.error("main","Invalid ACK Received Frome Client: {} expected: {}".format(rcvAckNum,expectedAckNum))
                            continue

                        if rcvSeqNum == expectedSeqNum:
                            ''' store msg, update new expected seq (cumulative) '''
                            nextExpectedSeqNum = rcvSeqNum + msgLength
                            nextExpectedSeqNum = socket.get_CumulativeACK(sender,nextExpectedSeqNum)
                            socket.set_ConnectionACK(sender,nextExpectedSeqNum) 
                            socket.add_ConnectionBuffer(msg)
                        elif rcvSeqNum < expectedSeqNum:
                            ''' dont store msg again - request our expectedSeqNum '''
                            nextExpectedSeqNum = expectedSeqNum
                            logFile.incr_Duplicate_ACK_Sent()
                            logFile.incr_Duplicate_Received()
                            event += "/DA"
                        else:
                            ''' store msg if required '''
                            nextExpectedSeqNum = expectedSeqNum
                            if socket.add_ConnectionBuffer(msg) is False:
                                logFile.incr_Duplicate_Received()
                            logFile.incr_Duplicate_ACK_Sent()
                            event += "/DA"
 
                        ''' send ack back to sender - request our expectedSeqNum '''
                        ackMsg = message.STPMessage()
                        ackMsg.set_Recipient(sender)
                        ackMsg.set_ACKNumber(nextExpectedSeqNum)
                        ackMsg.set_SequenceNumber(expectedAckNum) 
                        socket.sendACK(ackMsg,event)
                    else:
                        log.message.success("Client Connection Established")
                        if msg.is_FIN():
                            socket.tearDown(msg)
                            sys.exit() 
                        else:
                            ''' Third Handshake Ack is Ignored '''
                            pass

        except (OSError, ValueError) as err:
            log.message.error("main","{}".format(err))
        except KeyboardInterrupt:
            sys.exit()


if __name__== "__main__":
    args = arguments.receiverArgs(sys.argv)
    args.check()
    main(args)


