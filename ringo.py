import socket
import sys

from threading import Thread
import threading
import time

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

        self.pd_send_done = threading.Event()
        self.pd_rec_done = threading.Event()
        # self.pd_up_done = threading.Event()

    def run(self):
        while True:
            print 'Waiting for connection..'
            #Need to do peer discoery is when packet is FALSE
            data, address = self.socket.recvfrom(BUFFER_SIZE)
            print "Received connection from client"
            #print data
            #print 'Connected To', address
            if not data:
                continue
            if data.split(";")[0] == "PD":
                self.peer_discovery_append(address, data.split(";")[1])
                sender = threading.Thread(target=self.peer_discover_send).start()
                self.pd_send_done.wait()
            # elif data.split(";")[0] == "PDUP":
            #     update_server = threading.Thread(target=self.update_server, args=(data,address)).start()
            #     self.pd_up_done.wait()
            print "SERVER RINGO VECTOR"
            print self.ringo_vector

        #rec = threading.Thread(target=self.rec).start()

    def peer_discovery_append(self, client_address, server_port):
        print "PD Started"
        new_ringo = client_address + (server_port,)
        if new_ringo not in self.ringo_vector:
            self.ringo_vector.append(new_ringo)

    def peer_discover_send(self):
        response = "PDSENDACK;"
        for r in self.ringo_vector:
            response += str(r[0]) + "," + str(r[2]) + ";"
        for r in self.ringo_vector:
            r_addr = (r[0], int(r[2]))
            if r[0] != socket.gethostbyname(socket.gethostname()) or str(r[1]) != self.udp_port:
                print "ADDRESS TO SEND VECTOR TO"
                print r_addr
                self.socket.sendto(response, r_addr)
        time.sleep(2)
        self.pd_send_done.set()
        self.pd_send_done.clear()

    # def update_server(self, data, address):
    #     for d in data.split(";")[1:]:
    #         if d not in self.ringo_vector:
    #             self.ringo_vector.append(d)
    #     self.socket.sendto("UPACK", address)
    #     self.pd_up_done.set()
    #     self.pd_up_done.clear()


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

        self.pd_send_done = threading.Event()
        #print self.local_addr
        #Make so you have to do the gethostbyname function
        sender = threading.Thread(target=self.handle_pd).start()
        #self.send_pd()

    def run(self):
        while True:
            #print "Waiting to receive client!!!!!!!!!!!!!!!!!!"
            while not self.pd_send_done.isSet():
                print "Waiting to receive client!!!!!!!!!!!!!!!!!!"
                data, address = self.socket.recvfrom(BUFFER_SIZE)
                if data.split(";")[0] == "PDSENDACK":
                    self.respond_pd(data)
                    print "FINAL VECTOR IN CLIENT RUN"
                    print self.ringo_vector
            data = raw_input('> ')
            if not data:
                continue


    def handle_pd(self):
        if self.poc_name != "0" and self.poc_port != 0:
            print "SENDING"
            self.poc_addr = (self.poc_name, self.poc_port)
            self.socket.sendto("PD;" + str(self.udp_port), self.poc_addr)
        else:
            print "SENDING"
            self.socket.sendto("PD;" + str(self.udp_port), self.local_server_addr)

        print "Waiting to receive..."
        data, address = self.socket.recvfrom(BUFFER_SIZE)

        self.respond_pd(data)
        print "THIS IS THE FINAL VECTOR"
        print self.ringo_vector
        # ringo_up = ""
        # for r in self.ringo_vector:
        #     ringo_up = str(r[0]) + "," + str(r[1]) + "," + str(r[2]) + ";"
        #     time.sleep(2)
        #     print "UPDATING OWN SERVER"
        #     self.socket.sendto("PDUP;" + ringo_up, self.local_server_addr)
        #     data, address = self.socket.recvfrom(BUFFER_SIZE)
        time.sleep(1)
        self.pd_send_done.set()
        self.pd_send_done.clear()

    def respond_pd(self, data):
        #print "GOT HERE"
        for d in data.split(";")[1:]:
            if d not in self.ringo_vector:
                self.ringo_vector.append(d)
        self.ringo_vector.pop()
        # if self.poc_name != "0" and self.poc_port != 0:
        #     self.socket.sendto("PDRECACK", self.poc_addr)
        # else:
        #     self.socket.sendto("PDRECACK", self.local_server_addr)

class Server:
    def __init__(self, flag, udp_port, poc_name, poc_port, n):
        self.flag = flag
        self.udp_port = udp_port
        self.poc_name = poc_name
        self.poc_port = poc_port
        self.n = n
        self.ringo_vector = []
        self.pd_done = False
        self.cur_other_ringo_count = 0

        #self.pd_send_done = threading.Event()
        #print self.local_addr
        #Make so you have to do the gethostbyname function
        #sender = threading.Thread(target=self.handle_pd).start()
        #self.send_pd()

    def ringoServer(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        local_server_addr = (socket.gethostbyname(socket.gethostname()), self.udp_port)
        #local_addr = (socket.gethostbyname(socket.gethostname()), self.socket.getsockname()[1])
        sock.bind(('', self.udp_port))

        while True:
            #print 'Waiting for connection..'
            #Need to do peer discoery is when packet is FALSE
            data, address = sock.recvfrom(BUFFER_SIZE)
            #print "Received connection from client"
            #print data
            #print 'Connected To', address
            if not data:
                continue
            if data.split(";")[0] == "PD":
                self.peer_discovery_append(data.split(";")[1].split(",")[0], data.split(";")[1].split(",")[1])
                if len(self.ringo_vector) != self.n and self.pd_done == False:
                    update_vector = "PDUP;"
                    for r in self.ringo_vector:
                        update_vector += r[0] + "," + str(r[1]) + ";"
                    for r in self.ringo_vector:
                        if r != (socket.gethostbyname(socket.gethostname()), int(self.udp_port)):
                            sock.sendto(update_vector, r)

            if len(self.ringo_vector) == self.n and self.pd_done == False:
                self.pd_done = True
                final_vector = "PDDONE;"
                for r in self.ringo_vector:
                    final_vector += r[0] + "," + str(r[1]) + ";"
                for r in self.ringo_vector:
                    if r != (socket.gethostbyname(socket.gethostname()), int(self.udp_port)):
                        sock.sendto(final_vector, r)

            if data.split(";")[0] == "PDDONE":
                for d in data.split(";")[1:len(data.split(";"))-1]:
                    ringo_check = (d.split(",")[0], int(d.split(",")[1]))
                    if ringo_check not in self.ringo_vector:
                        self.ringo_vector.append(ringo_check)
                #self.ringo_vector.pop()
                #self.curRingoCount += 1
                print self.ringo_vector

            # if len(self.ringo_vector) != self.n and self.pd_done == False:
            # #    print "updating"
            #     update_vector = "PDUP;"
            #     for r in self.ringo_vector:
            #         update_vector += r[0] + "," + str(r[1]) + ";"
            #     for r in self.ringo_vector:
            #         if r != (socket.gethostbyname(socket.gethostname()), int(self.udp_port)):
            #             sock.sendto(update_vector, r)

            if data.split(";")[0] == "PDUP":
                for d in data.split(";")[1:len(data.split(";"))-1]:
                    ringo_check = (d.split(",")[0], int(d.split(",")[1]))
                    if ringo_check not in self.ringo_vector:
                        self.peer_discovery_append(d.split(",")[0], d.split(",")[1])

            #print "SERVER RINGO VECTOR"
            print self.ringo_vector

    def peerDiscovery(self):
        print "PD Starting"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        local_server_addr = (socket.gethostbyname(socket.gethostname()), self.udp_port)
        #local_addr = (socket.gethostbyname(socket.gethostname()), self.socket.getsockname()[1])
        sock.bind(('',0))
        #if (socket.gethostbyname(socket.gethostname()), self.udp_port) not in self.ringo_vector:
        self.ringo_vector.append((socket.gethostbyname(socket.gethostname()), self.udp_port) )
        print "APPENDED INITIAL"
        #self.peer_discovery_append(socket.gethostbyname(socket.gethostname()), self.udp_port)

        if self.poc_name != "0" and self.poc_port != 0:
            self.peer_discovery_append(socket.gethostbyname(self.poc_name), self.poc_port)

        #print self.curRingoCount
        while self.cur_other_ringo_count < self.n:
        #    print self.ringo_vector
            pdPacket = "PD;"
            for r in self.ringo_vector:
                pdPacket += r[0] + "," + str(r[1]) + ";"

            for r in self.ringo_vector:
                if r != (socket.gethostbyname(socket.gethostname()), self.udp_port):
                #    print "Sending to"
                #    print r
                    sock.sendto(pdPacket, r)
        #print self.ringo_vector


    def peer_discovery_append(self, client_address, server_port):
        new_ringo = (client_address, int(server_port))
        if new_ringo not in self.ringo_vector:
            self.ringo_vector.append(new_ringo)
            self.cur_other_ringo_count += 1


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
    N = int(sys.argv[5])

    server = Server(FLAG, UDP_PORT, POC_NAME, POC_PORT, N)

    Thread(target=server.peerDiscovery).start()
    Thread(target=server.ringoServer).start()


    # server = Server(FLAG, UDP_PORT, POC_NAME, POC_PORT, N)
    # client = Client(FLAG, UDP_PORT, POC_NAME, POC_PORT, N)
    #
    # server.start()
    # client.start()
    # server.join()
