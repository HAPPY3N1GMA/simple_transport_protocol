#! /usr/bin/env python3.6

import sys,time,datetime,string,random,threading, time, signal
from classes import arguments, protocol, threads, defines, log
from os import sys

def main(args):
    ''' initialise random number generator '''
    random.seed(args.get_seed())

    ''' initialise STP protocol '''
    socket = protocol.STPSender()
    socket.set_Args(args)
    socket.init_window_frame()
    socket.connect()
    try:
        ''' init PLD Module and file segments'''
        socket.init_PLD()
        socket.init_msg_queue()
        try:
            ''' create sender thread '''
            senderThread = threads.senderThread(socket)
            senderThread.start()

            signal.signal(signal.SIGTERM, threads.terminate_thread)
            signal.signal(signal.SIGINT, threads.terminate_thread)
    
            while defines.uploading:
                ''' listen for ACKS from the server'''
                msg = socket.listen()
                if msg is not None and msg.is_ACK():
                    defines.uploading = socket.update_window(msg)

            senderThread.shutdown_flag.set()
            senderThread.join()
            print("\n")
        except threads.ServiceExit:
            ''' Force Kill File Upload Gracefully '''
            senderThread.shutdown_flag.set()
            senderThread.join()
    except:
        pass
    socket.tearDown()

if __name__== "__main__":
    args = arguments.senderArgs(sys.argv)
    args.check()
    main(args)


