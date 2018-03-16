import socket
import sys

from threading import Thread
import numpy as np

class Server(Thread):
    def __init__(self, flag, udp_port, poc_name, poc_port, n):
        Thread.__init__(self)
        self.flag = flag
        self.udp_port = udp_port
        self.poc_name = poc_name
        self.poc_port = poc_port
        self.n = n

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.local_server_addr = (socket.gethostbyname(socket.gethostname()), self.udp_port)
        self.socket.bind(self.local_server_addr)

        self.ringo_vector = []
        #if self.poc_name == "0" and self.poc_port == 0:
            #self.ringo_vector.append(self.local_server_addr)
            #print self.ringo_vector

    def run(self):
        while True:
            print 'Waiting for connection..'
            #Need to do peer discoery is when packet is FALSE
            data, address = self.socket.recvfrom(BUFFER_SIZE)
            #print 'Connected To', address
            if not data:
                continue
            if data.split(";")[0] == "PD":
                self.peer_discovery_append(address, data.split(";")[1])
                self.peer_discover_send()
            #else:
            #    self.socket.sendto(data, address)

    def peer_discovery_append(self, client_address, server_port):
        print "PD Started"
        new_ringo = client_address + (server_port,)
        print new_ringo
        if new_ringo not in self.ringo_vector:
            self.ringo_vector.append(new_ringo)
        #response = ""
        #for r in self.ringo_vector:
        #    response += str(r[0]) + "," + str(r[1]) + ";"
        #self.socket.sendto(response, address)

    def peer_discover_send(self):
        response = "PDSENDACK;"
        for r in self.ringo_vector:
            response += str(r[0]) + "," + str(r[2]) + ";"
        for r in self.ringo_vector:
            r_addr = (r[0], int(r[1]))
            #print r_addr
            self.socket.sendto(response, r_addr)
            data, address = self.socket.recvfrom(BUFFER_SIZE)
            #print data


class Client(Thread):
    def __init__(self, flag, udp_port, poc_name, poc_port, n):
        Thread.__init__(self)
        self.flag = flag
        self.udp_port = udp_port
        self.poc_name = poc_name
        self.poc_port = poc_port
        self.n = n
        self.ringo_vector = []


        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.local_server_addr = (socket.gethostbyname(socket.gethostname()), self.udp_port)
        self.local_addr = (socket.gethostbyname(socket.gethostname()), self.socket.getsockname()[1])
        #print self.local_addr
        #Make so you have to do the gethostbyname function
        if self.poc_name != "0" and self.poc_port != 0:
            print "SENDING"
            self.poc_addr = (self.poc_name, self.poc_port)
            self.socket.sendto("PD;" + str(self.udp_port), self.poc_addr)
        else:
            self.socket.sendto("PD;" + str(self.udp_port), self.local_server_addr)

    def run(self):
        while True:
            #self.socket.sendto("PD", self.poc_addr)
            # data = raw_input('> ')
            # if not data:
            #     continue
            # self.socket.sendto(data, self.poc_addr)
            data, address = self.socket.recvfrom(BUFFER_SIZE)
            if data.split(";")[0] == "PDSENDACK":
                for d in data.split(";")[1:]:
                    if d not in self.ringo_vector:
                        self.ringo_vector.append(d)
                self.ringo_vector.pop()
                if self.poc_name != "0" and self.poc_port != 0:
                    self.socket.sendto("PDRECACK", self.poc_addr)
                else:
                    self.socket.sendto("PDRECACK", self.local_server_addr)
            #print data
            print self.ringo_vector
            # if data == "PD":
            #     response_split = response.split(";")
            #     response_split.pop()
            #     for r in response_split:
            #         r_split = r.split(",")
            #         self.socket.sendto(data, (r_split[0], int(r_split[1])))
            #         pd_response, server = self.socket.recvfrom(BUFFER_SIZE)
            #         print pd_response

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
    #FIX LATER
    #UDP_PORT = 50000
    #if int(sys.argv[2]) > 49152 and int(sys.argv[2]) < 65535:
    UDP_PORT = int(sys.argv[2])
    BUFFER_SIZE = 1024
    POC_NAME = sys.argv[3]
    POC_PORT = int(sys.argv[4])
    N = sys.argv[5]


    server = Server(FLAG, UDP_PORT, POC_NAME, POC_PORT, N)
    client = Client(FLAG, UDP_PORT, POC_NAME, POC_PORT, N)

    server.start()
    client.start()
    server.join()
