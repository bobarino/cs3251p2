import socket
import sys
import time
import requests

from threading import Thread
import numpy as np

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
        self.n = n
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
            print response
            # if data == "PD":
            #     response_split = response.split(";")
            #     response_split.pop()
            #     for r in response_split:
            #         r_split = r.split(",")
            #         self.socket.sendto(data, (r_split[0], int(r_split[1])))
            #         pd_response, server = self.socket.recvfrom(BUFFER_SIZE)
            #         print pd_response







# -----------------------------------------------------
# i wrote this assuming the dest ringo is param idk#
#def rtt_calc(dest):
#    # initial time when sent
#    initialTime = time.time()
#    
#    reqTime = requests.get(dest)
#
     # time of ack
#    finalTime = time.time()

#    totalTime = str(finalTime - initialTime)






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
