import socket
import sys
import time
import requests

from threading import Thread
# import numpy as np
# import pandas as pd

class Packet:
    pDEL = '$$$'
    DEL = '@'

    def __init__(self_):
        self.src = ''
        self.src_port = 0
        self.dest = ''
        self.dest_port = 0
        self.seqNum = 0
        self.ackNum = 0
        self.data = ''
        self.pd_flag = False
        self.ack_flag = False

    def pack(self):
        seq = (str(self.src), str(self.src_port), str(self.dest), str(self.dest_port), str(self.seqNum), str(self.ackNum), str(self.data), str(self.pd_flag), str(self.ack_flag))
        DEL.join(seq)
        packed = seq + pDEL
        return packed

    def unpack(self, packed):
        seq = string(packed).split(DEL)
        self.src = seq[0]
        self.src_port = seq[1]
        self.dest = seq[2]
        self.dest_port = seq[3]
        self.seqNum = seq[4]
        self.ackNum = seq[5]
        self.data = seq[6]
        
        if seq[7] == 'True':
            self.pd_flag = True
        else:
            self.pd_flag = False

        if seq[8] == 'True':
            self.ack_flag = True
        else:
            self.ack_flag = False


class Server(Thread):
    def __init__(self, host, port):
        Thread.__init__(self)
        self.port = port
        self.host = host
        self.bufsize = 1024
        self.addr = (host, port)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(self.addr)

        self.ringo_vector = []

    def run(self):
        while True:
            #print 'Waiting for connection..'
            data, address = self.socket.recvfrom(BUFFER_SIZE)
            #print 'Connected To', address
            if address not in self.ringo_vector:
                self.ringo_vector.append(address)
            if not data:
                continue
            if data == "PD":
                response = ""
                for r in self.ringo_vector:
                    response += str(r[0]) + "," + str(r[1]) + ";"
                self.socket.sendto(response, address)
            else:
                self.socket.sendto(data, address)

class Client(Thread):
    def __init__(self, flag, host, port, n):
        Thread.__init__(self)
        self.flag = flag
        self.port = port
        self.host = host
        .n = n
        self.bufsize = 1024
        self.addr = (host, port)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def run(self):
        while True:
            data = raw_input('> ')
            if not data:
                continue
            self.socket.sendto(data, self.addr)
            response, server = self.socket.recvfrom(BUFFER_SIZE)
            print (response)
            # if data == "PD":
            #     response_split = response.split(";")
            #     response_split.pop()
            #     for r in response_split:
            #         r_split = r.split(",")
            #         self.socket.sendto(data, (r_split[0], int(r_split[1])))
            #         pd_response, server = self.socket.recvfrom(BUFFER_SIZE)
            #         print pd_response




# -----------------------------------------------------
def assignRingoID(pd_vector):
    c = 0
    for ringo in pd_vector:
        ringo.id = c
        c = c +1

def rtt_calc(self, dest):
    # initial time when sent
    initialTime = time.time()

    # this is probs wrong
    # basically need to ping and get something back
    reqTime = requests.get(dest)

     # time of ack
    finalTime = time.time()

    totalTime = str(finalTime - initialTime)
    return totalTime

def make_rtt_matrix(self, N):
    distances = {}
    for ringo in pd_vector:
        for r in pd_vector:
            # calculates distance
            d = rtt_calc(ringo, r)
            # makes tuple of ringos to act as dict key
            t = (ringo, r)
            # puts key in dict with distance as value
            distances[t] = d

                    
def calc_optimal_ring_form(self):
    path = []
    cost = 0




if __name__ == "__main__":

    if len(sys.argv) != 6:
        print "You must enter the flag as your first argument (S, R, or F)."
        # S: sender, R; receiver, F: forwarder
        print "You must enter in a port number as your second argument. If not entered within 49152 and 65535 (exclusive), it will default to 50000."
        print "You must enter in the host-name of the PoC for this Ringo (0 if it doesn't have one) as your 3rd argument."
        print "You must enter in the UDP port number of the PoC for this Ringo (0 if it doesn't have one) as your 4th argument."
        print "You must enter in the total number or Ringos as the last argument."
        sys.exit(1)

    FLAG = sys.argv[1]
    UDP_PORT = 50000
    if int(sys.argv[2]) > 49152 and int(sys.argv[2]) < 65535:
        UDP_PORT = int(sys.argv[2])
    BUFFER_SIZE = 1024
    POC_NAME = sys.argv[3]
    POC_PORT = int(sys.argv[4])
    N = sys.argv[5]


    server = Server(POC_NAME, UDP_PORT)
    client = Client(FLAG, POC_NAME, POC_PORT, N)

    server.start()
    client.start()
    server.join()
