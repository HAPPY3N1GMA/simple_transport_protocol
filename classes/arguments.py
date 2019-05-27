#! /usr/bin/env python3.6

from os import sys
import collections,ipaddress
from abc import ABCMeta, abstractmethod
from classes import defines,defines,log



class arg(object):
    ''' Initialise arguments Object '''
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self,argv):
        pass

    def set_Receiver_host_ip(value):
        ''' Set Argument Host IP '''
        self._receiver_host_ip = value


    def set_Receiver(receiver: tuple):
        ''' Set Argument Receiver '''
        set_Receiver_host_ip(receiver[0])
        set_Receiver_host_ip(receiver[1])

    def set_Receiver_port(value):
        ''' Set Argument Receiver Port '''
        self._receiver_port = value


    def get_receiver_host_ip(self):
        ''' get argument receiver_host_ip '''
        return self._receiver_host_ip


    def get_receiver(self):
        return ((self.get_receiver_host_ip(),self.get_receiver_port()))


    @abstractmethod
    def check(self):
        pass


    def get_receiver_port(self):
        ''' get argument receiver_port '''
        return self._receiver_port


    def get_filename(self):
        ''' get argument filename '''
        return self._filename


    def getReceipient(self):
        ''' returns tuple containing ip and port of target '''
        return ((self.get_receiver_host_ip(), self.get_receiver_port()))


    def assign(self,variable,value,typeFloat=True):
        ''' Set Variable Values '''
        try:
            if typeFloat:
                setattr(self, variable, float(value))
            else:
                setattr(self, variable, int(value))
        except:
            setattr(self, variable, None)


    def printArgs(self,variable):
        ''' Print Program Arguments '''
        return "{} : {}".format(variable,getattr(self, variable))


    def logArgs(self):
        ''' Print Arguments and their names'''
        log.message.default("{} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {}".format(
            self.printArgs('_max_window_size'),
            self.printArgs('_max_segment_size'),
            self.printArgs('_gamma'),
            self.printArgs('_pDrop'),
            self.printArgs('_pDuplicate'),
            self.printArgs('_pCorrupt'),
            self.printArgs('_pOrder'),
            self.printArgs('_maxOrder'),
            self.printArgs('_pDelay'),
            self.printArgs('_maxDelay'),
            self.printArgs('_seed')))


class senderArgs(arg):
    ''' Sender arguments '''
    def __init__(self,argv):
        arg_names = [
            'receiver_host_ip', # The IP address of the host machine on which the Receiver is running.
            'receiver_port', # The port number on which Receiver is expecting to receive packets from the sender.
            'filename', # The name of the pdf file that has to be transferred from sender to receiver using your STP.
            'max_window_size', # The maximum window size used by your STP protocol in bytes.
            'max_segment_size', # Maximum Segment Size which is the maximum amount of data (in bytes) carried in each STP segment
            'gamma', # This value is used for calculation of timeout value.
            'pDrop', # The probability that a STP data segment which is ready to be transmitted will be dropped.
            'pDuplicate', # The probability that a data segment which is not dropped will be duplicated.
            'pCorrupt', # The probability that a data segment which is not dropped/duplicated will be corrupted.
            'pOrder', # The probability that a data segment which is not dropped, duplicated and corrupted will be re-ordered.
            'maxOrder', # The maximum number of packets a particular packet is held back for re-ordering purpose.
            'pDelay', # The probability that a data segment which is not dropped, duplicated, corrupted or re-ordered will be delayed.
            'maxDelay', # The maximum delay (in milliseconds) experienced by those data segments that are delayed.
            'seed'] # The seed for your random number generator.
        
        arg_list = collections.namedtuple('arg_list', arg_names)
        args = dict(zip(arg_names, argv[1:]))
        args = arg_list(*(args.get(arg, None) for arg in arg_names))

        arg_list(receiver_host_ip='127.0.0.1', receiver_port='1111', filename='test1.pdf', max_window_size='10000', max_segment_size='100000', gamma=None, pDrop=None, pDuplicate=None, pCorrupt=None, pOrder=None, maxOrder=None, pDelay=None, maxDelay=None, seed=None)

        self._receiver_host_ip = args[0]
        self.assign('_receiver_port',args[1],False)
        self._filename = args[2]
        self.assign('_max_window_size',args[3],False)
        self.assign('_max_segment_size',args[4],False)
        self.assign('_gamma',args[5])
        self.assign('_pDrop',args[6])
        self.assign('_pDuplicate',args[7])
        self.assign('_pCorrupt',args[8])
        self.assign('_pOrder',args[9])
        self.assign('_maxOrder',args[10],False)
        self.assign('_pDelay',args[11])
        self.assign('_maxDelay',args[12],False)
        self.assign('_seed',args[13])

        ''' Print Arguments '''
        self.logArgs()


    def get_max_window_size(self):
        ''' get argument max_window_size '''
        return self._max_window_size


    def get_max_segment_size(self):
        ''' get argument max_segment_size '''
        return self._max_segment_size


    def get_gamma(self):
        ''' get argument gamma '''
        return self._gamma


    def get_pDrop(self):
        ''' get argument pDrop '''
        return self._pDrop


    def get_pDuplicate(self):
        ''' get argument pDuplicate '''
        return self._pDuplicate


    def get_pCorrupt(self):
        ''' get argument pCorrupt '''
        return self._pCorrupt


    def get_pOrder(self):
        ''' get argument pOrder '''
        return self._pOrder


    def get_maxOrder(self):
        ''' get argument maxOrder '''
        return self._maxOrder


    def get_pDelay(self):
        ''' get argument pDelay '''
        return self._pDelay


    def get_maxDelay(self):
        ''' get argument maxDelay '''
        return self._maxDelay


    def get_seed(self):
        ''' get argument seed '''
        return self._seed


    def check(self):
        ''' Check Minimum arguments Set '''
        try:
            assert(self.get_receiver_host_ip()),"No IP Specified"
            try:
                assert(ipaddress.IPv4Address(self.get_receiver_host_ip())),"Invalid IPV4 Address"
            except:
                log.message.error("Invalid Arguments","Invalid IPV4 Address")
                sys.exit()
            assert(self.get_receiver_port() is not None),"No Port Specified"
            assert(self.get_filename() is not None),"No File Specified"
            assert(self.get_max_window_size() is not None),"No MWS Specified"
            assert(self.get_max_window_size() is not None and self.get_max_window_size() >= 1), "MWS must be >= 1"
            assert(self.get_max_segment_size() is not None),"No MSS Specified"
            assert(self.get_max_segment_size() is not None and self.get_max_segment_size() >= 1), "MWS must be >= 1"
            assert(self.get_gamma() is not None and self.get_gamma() >=0), "Gamma must be >= 0"

            ''' PLD Arguments '''
            assert(self.get_pDrop() is not None and self.get_pDrop() >= 0 and self.get_pDrop() <= 1), "pDrop must be between 0 and 1"
            assert(self.get_pDuplicate() is not None and self.get_pDuplicate() >= 0 and self.get_pDuplicate() <= 1), "pDuplicate must be between 0 and 1"
            assert(self.get_pCorrupt() is not None and self.get_pCorrupt() >= 0 and self.get_pCorrupt() <= 1), "pCorrupt must be between 0 and 1"
            assert(self.get_pOrder() is not None and self.get_pOrder() >= 0 and self.get_pOrder() <= 1), "pOrder must be between 0 and 1"
            assert(self.get_maxOrder() is not None and (self.get_pOrder() == 0 or (self.get_maxOrder() >= 1 and self.get_maxOrder() <= 6))), "MaxOrder must be between 1 and 6"
            assert(self.get_pDelay() is not None and self.get_pDelay() >= 0 and self.get_pDelay() <= 1), "pDelay must be between 0 and 1"
            assert(self.get_maxDelay() is not None and self.get_maxDelay() >= 0), "MaxDelay must be >= 0"
            assert(self.get_seed() is not None), "No Seed Specified"

        except AssertionError as e:
            log.message.error("Invalid Arguments",e)
            sys.exit()


class receiverArgs(arg):
    ''' Receiver arguments '''
    def __init__(self,argv):
        arg_names = [
            'receiver_port', # The IP address of the host machine on which the Receiver is running.
            'filename']

        arg_list = collections.namedtuple('arg_list', arg_names)
        args = dict(zip(arg_names, argv[1:]))
        args = arg_list(*(args.get(arg, 0) for arg in arg_names))

        try:
            self.assign('_receiver_port',args[0],False)
            self._receiver_host_ip = '127.0.0.1'
            self._filename = args[1]
        except:
            pass


    def check(self):
        ''' Check Minimum arguments Set '''
        try:
            assert(self.get_receiver_port()),"No Port Specified"
            assert(self.get_filename()),"No File Specified"

        except AssertionError as e:
            print("Invalid arguments: ",e)
            sys.exit()


