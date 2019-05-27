#! /usr/bin/env python3.6

from socket import *
from enum import IntFlag, auto


class Perm(IntFlag):
    ''' Bitwise Permission Flags '''
    DEFAULT = 0
    SYN = auto()
    ACK = auto()
    SYNACK = SYN|ACK
    FIN = auto()


class Status(IntFlag):
    ''' Msg Status '''    
    DEFAULT = 0
    SENT = auto()
    TIMEOUT = auto()
    RECEIVED = auto()
    RECEIVED_2 = RECEIVED + 1
    RECEIVED_3 = RECEIVED + 2


CRLF = "\r\n"
UDPSOCKET = SOCK_DGRAM
TCPSOCKET = SOCK_STREAM
BUFFER_SIZE = 64000

''' Default Timeout Values as per Textbook '''
ALPHA = 0.125
BETA = 0.25
ESTIMATEDRTT = 500 # 500 milliseconds
DEVRTT = 250 # 250 milliseconds
TIMEOUT = 1000 # 1000 milliseconds

APPEND = "a"
WRITE = "w"
WRITE_BYTE = "wb"
READ_BYTE = "rb"

SUCCESS = 0
CORRUPT = 1
FAILURE = 2

uploading = True