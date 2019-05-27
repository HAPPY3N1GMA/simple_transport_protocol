# Simple Transport Protocol #

This protocol was designed using Python3 and is not compatible with prior versions.

```
python3.6 sender.py <Arguments>
python3.6 receiver.py <Arguments>

or

./sender.py <Arguments>
./receiver.py <Arguments>
```

## Implementation and Features
Below are overviews of the key features implemented.

### sender.py ###
The STP Sender is divided into two main components, ​ listener ​ ​ and ​ sender ​ threads. They work together to manage the clients network connection, file transfer, PLD and logging.

#### Listener ​ - operated by the main thread, its primary operations include:

	1. Initialising the STP Protocol:
		a. Storing the program Arguments
		b. Opening the file, breaking it up into chunks and queuing into MSS segments
		c. Initialising the sending window of MWS
		d. Connecting to the remote server using a three-segment (SYN, SYN/ACK, ACK) handshake

	2. Initialising the PLD Module for use by the Sender Thread

	3. Creating and starting a Sender Thread
	
	4. Listening for incoming ACK requests:
		a. Receive incoming segments and unpacking into a message object

	5. Updating the message window:
		a. Update log with received message stats
		b. Update Estimated RTT and RTO
		c. Update message window if required
		d. If duplicate ACK:
			i. Updating duplicate ACK count
			ii. Carrying out Fast ReTransmission if required, and subsequently cancelling RTT calculation
		e. Signal if file transfer completed

	6. Terminating the Sender Thread

	7. Closing the remote connection:
		a. Complete a four-segment (FIN, ACK, FIN, ACK) teardown
		b. Write final PLD Log Statistics
		c. Program closure

#### Sender ​ - operated by the spawned secondary thread, its primary operations include:
1. Calculation of Timeout Events
	a. Logging of Timeout Events
	b. Restarting Timeout Timer
	c. Cancelling active RTT calculation

2. Sending new, unsent segments from the message window

3. Operating the PLD module
	a. Calculation and execution of PLD events - ie message dropping, corruption etc
	b. Logging of PLD events
	c. Creating delayed message threads as required
	d. Final transmission of segments over UDP network


### receiver.py
The STP Receiver is a single threaded system. It manages the servers STP Protocol, network connections, file
buffering, logging and file output. Its primary operations are:

	1. Initialising the STP Protocol:
		a. Storing the program arguments
		b. Creating a listening UDP socket
	
	2. Connection Management
		a. Initialising a new client connection
		b. Completing three-segment (SYN, SYN/ACK, ACK) handshake
		c. Buffering out of order message segments
		d. Managing Cumulative Acknowledgments
		e. Managing Sequence/Ack Numbers
		f. Sending/Receiving Messages
		g. Completing a four-segment (FIN, ACK, FIN, ACK) teardown

	3. Message Operations
		a. Unpacking received STP segments
		b. STP corruption checks
		c. Packing of STP segments for sending
	4. File Logging
		a. Logging of received and sent files
		b. Logging of STP statistics

### STP HEADER
The header I designed is 88 bits in size and contains 4 fields with the variable sized payload following. The
fields used are as follows:
	i. SEQ NUMBER - Increment from 0 by bytes of data (32 bits)
	ii. ACK NUMBER - Increment from 0 by bytes of data (32 bits)
	iii. FLAGS - Bitwise Flags (SYN, ACK, SYN/ACK, FIN) (8 bits)
	iv. CHECKSUM - Checksum of the STP Segment (includes payload) (16 bits)
	v. PAYLOAD - Transmitted data of variable length





