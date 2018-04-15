import pickle

class Packet:
    def __init__(self, header, data):
        self.head = header
        self.data = data

#Fletcher-32 checksum
def calculate_checksum(data):
	b = bytearray(data)
	result = sum(b) % 65535
	return result

#Packet Types:
#PD -> Peer discovery
#PDUP -> Update peer discovery ringo vector
#PDDONE -> Finished peer discovery
#RTTSEND -> Sent data for RTT time
#RTTREC -> Received data back for RTT time
#RTTVEC -> Getting completed RTT vectors to add to matrix
#RTTDONE -> Finished RTT matrix
#FLAG -> Got flag request
#RECFLAG -> Received flag from ringo
#KA -> Keep Alive
#KAACK -> Keep Alive Acknowledgment
#FILE -> Got filename
#DSEND -> Got data
#DACK -> Acknowledge that correct data was received
#DDONE -> Finished with data retrieval
#PDREV -> After ringo comes back from offline, get peer discovery info from Receiver (can't go offline)
#PDREVDONE -> PD Revival is done for offline ringo
#RTTREV (Outdated?) -> Tell all ringos to redo rtt_matrix
#RTTREDO -> Restart RTT after an offline ringo comes back online

def create_packet(srcPort, destPort, seqNum, ackNum, packType, data):
    header = "$$" + str(srcPort) + "%" + str(destPort) + "%" + str(seqNum) + "%" + str(ackNum) + "%" + str(packType) + "%"
    checkSum = calculate_checksum(header + data)
    header += str(checkSum) + "$$"
    finalPacket = Packet(header, data)
    return finalPacket

def deconstruct_packet(packet):
    deconstructed = packet.head.replace("$$", "").split(";")
    deconstructed.append(packet.data)
    return deconstructed

def packet_to_bytes(packet):
    byteString = pickle.dumps(packet)
    return byteString

def bytes_to_packet(bytestream):
    reassembled_packet = pickle.loads(bytestream)
    return reassembled_packet
