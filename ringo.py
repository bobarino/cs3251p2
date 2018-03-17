import socket
import sys

from threading import Thread
import threading
import time

class Server:
    def __init__(self, flag, udp_port, poc_name, poc_port, n):
        self.flag = flag
        self.udp_port = udp_port
        self.poc_name = poc_name
        self.poc_port = poc_port
        self.n = n
        self.ringo_vector = []
        self.pd_done = 0
        self.cur_other_ringo_count = 0
        self.rtt_vector = []
        self.rtt_matrix = []
        self.flag_dic = {}

        #self.pd_send_done = threading.Event()
        #print self.local_addr
        #Make so you have to do the gethostbyname function
        #sender = threading.Thread(target=self.handle_pd).start()
        #self.send_pd()

    def ringo_server(self):
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
                if len(self.ringo_vector) != self.n and self.pd_done == 0:
                    sender = threading.Thread(target=self.peer_discover_blast, args=(sock,)).start()

            if len(self.ringo_vector) == self.n and self.pd_done == 0:
                self.pd_done = 1
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
                for r in self.ringo_vector:
                    #if r != (socket.gethostbyname(socket.gethostname()), int(self.udp_port)):
                        sock.sendto("FLAG;", r)
                rtt = threading.Thread(target=self.ringo_rtt_loop, args=(sock,)).start()
                #print "Discovered Peers"
                #print self.ringo_vector

            if data.split(";")[0] == "PDUP":
                for d in data.split(";")[1:len(data.split(";"))-1]:
                    ringo_check = (d.split(",")[0], int(d.split(",")[1]))
                    if ringo_check not in self.ringo_vector:
                        self.peer_discovery_append(d.split(",")[0], d.split(",")[1])

            if data.split(";")[0] == "RTTSEND":
                data_rec = "RTTREC;" + data.split(";")[1]
                sock.sendto(data_rec, address)

            if data.split(";")[0] == "RTTREC":
                self.rtt_recv(time.time(), data.split(";")[1], address, sock)

            if data.split(";")[0] == "RTTVEC":
                self.add_vec_to_matrix(data, sock)

            if data.split(";")[0] == "RTTDONE":
                self.sync_matrix(data)
                time.sleep(5)
                input_thread = threading.Thread(target=self.user_input, args=(sock,)).start()

            if data.split(";")[0] == "FLAG":
                send_flag = "RECFLAG;" + self.flag
                sock.sendto(send_flag, address)

            if data.split(";")[0] == "RECFLAG":
                self.flag_dic[address] = data.split(";")[1]


            #print "SERVER RINGO VECTOR"
            #print self.ringo_vector

    def peer_discovery(self):
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

        while self.cur_other_ringo_count < self.n:
            pdPacket = "PD;"
            for r in self.ringo_vector:
                pdPacket += r[0] + "," + str(r[1]) + ";"

            for r in self.ringo_vector:
                if r != (socket.gethostbyname(socket.gethostname()), self.udp_port):
                    sock.sendto(pdPacket, r)
                    time.sleep(1)

    def peer_discovery_append(self, client_address, server_port):
        new_ringo = (client_address, int(server_port))
        if new_ringo not in self.ringo_vector:
            self.ringo_vector.append(new_ringo)
            self.cur_other_ringo_count += 1

    def peer_discover_blast(self, sock):
        #time.sleep(2)
        #print "threading"
        update_vector = "PDUP;"
        for r in self.ringo_vector:
            update_vector += r[0] + "," + str(r[1]) + ";"
        for r in self.ringo_vector:
            if r != (socket.gethostbyname(socket.gethostname()), int(self.udp_port)):
                sock.sendto(update_vector, r)

    def rtt_calc(self, dest, sock):
        # initial time when sent
        initialTime = time.time()
        msg = "RTTSEND;" + str(initialTime)
        sock.sendto(msg, dest)


    def rtt_recv(self, final, initial, address, sock):
        my_t = ((socket.gethostbyname(socket.gethostname()), int(self.udp_port)), (socket.gethostbyname(socket.gethostname()), int(self.udp_port)), 0.0)
        if my_t not in self.rtt_vector:
            #self.rtt_vector[my_t] = 0
            self.rtt_vector.append(my_t)
        t = ((socket.gethostbyname(socket.gethostname()), int(self.udp_port)), address, final - float(initial))
        if t not in self.rtt_vector:
            self.rtt_vector.append(t)
        #self.rtt_vector[t] = final - float(initial)
        if len(self.rtt_vector) == self.n:
            #self_t = ((socket.gethostbyname(socket.gethostname()), self.udp_port), (socket.gethostbyname(socket.gethostname()), self.udp_port), 0)
            #if self_t not in self.rtt_matrix:
            #    self.rtt_matrix.append(self_t)
            for rtt in self.rtt_vector:
                t_add = (rtt[0], rtt[1], rtt[2])
                if t_add not in self.rtt_matrix:
                    self.rtt_matrix.append(t_add)
            send_vec = "RTTVEC;"
            #for key, value in self.rtt_vector.iteritems():
            for rtt in self.rtt_vector:
                send_vec += str(rtt[0][0]) + "," + str(rtt[0][1]) + "," + str(rtt[1][0]) + "," + str(rtt[1][1]) + "," + str(rtt[2]) + ";"
            for r in self.ringo_vector:
                if r != (socket.gethostbyname(socket.gethostname()), int(self.udp_port)):
                    sock.sendto(send_vec, r)
        # print len(self.rtt_vector)

    def add_vec_to_matrix(self, data, sock):
        for d in data.split(";")[1:len(data.split(";"))-1]:
            t = ((d.split(",")[0], int(d.split(",")[1])), (d.split(",")[2], int(d.split(",")[3])), float(d.split(",")[4]))
            if t not in self.rtt_matrix:
                self.rtt_matrix.append(t)
        if len(self.rtt_matrix) == self.n * self.n and self.poc_name == "0" and self.poc_port == 0:
            time.sleep(2)
            send_matrix = "RTTDONE;"
            for rtt in self.rtt_matrix:
                send_matrix += str(rtt[0][0]) + "," + str(rtt[0][1]) + "," + str(rtt[1][0]) + "," + str(rtt[1][1]) + "," + str(rtt[2]) + ";"
            for r in self.ringo_vector:
                #if r != (socket.gethostbyname(socket.gethostname()), int(self.udp_port)):
                sock.sendto(send_matrix, r)
            # print send
            # print "FINAL MATRIX"
            # print self.rtt_matrix
            # print len(self.rtt_matrix)

    # def format_matrix(self):
    #     for rtt in self.rtt_matrix:


    def sync_matrix(self, data):
        self.rtt_matrix = []
        #print self.rtt_matrix
        for d in data.split(";")[1:len(data.split(";"))-1]:
            t = ((d.split(",")[0], int(d.split(",")[1])), (d.split(",")[2], int(d.split(",")[3])), float(d.split(",")[4]))
            if t not in self.rtt_matrix:
                self.rtt_matrix.append(t)
        #print self.rtt_matrix

    def calc_optimal_ring_form(self, sock):
        path = []
        forwarder = []
        for key, value in self.flag_dic.iteritems():
            if value == 'S':
                path = key
            elif value == 'F':
                forwarder.append(key)
            else:
                final = key

        small = []
        if len(forwarder) == 0:
            small.append(path[1])
            small.append(final[1])
        elif len(forwarder) == 1:
            small.append(path[1])
            small.append(forwarder[0][1])
            small.append(final[1])
        else:
            #self.shortest_path(path[-1], final[-1])
            #self.travelling_salesman(self.rtt_matrix, path[-1])
            #self.find_path(self.rtt_matrix, path[-1], final[-1])
            cur_src = path[-1]
            rem = len(forwarder)
            small.append(cur_src)
            visited = []
            visited.append(cur_src)
            while rem > 0:
                # gets most recent path visit
                cur_cost = 99999999
                for rtt in self.rtt_matrix:
                    if rtt[0][1] == cur_src:
                        if rtt[2] != 0.0 and rtt[2] < cur_cost and rtt[1][1] not in visited:
                            cur_src = rtt[1][1]
                            visited.append(rtt[1][1])
                            cur_cost = rtt[2]
                small.append(cur_src)
                rem -= 1
            small.append(final[1])

        return small

    # def shortest_path(self, start, end):
    #     for rtt in self.matrix:



    def ringo_rtt_loop(self, sock):
        for r in self.ringo_vector:
            if r != (socket.gethostbyname(socket.gethostname()), int(self.udp_port)):
                self.rtt_calc(r, sock)

    def user_input(self, sock):
        #print self.flag_dic
        #print self.rtt_matrix
        data = raw_input('> ')
        if data == "show-matrix":
            print self.rtt_matrix
            self.user_input(sock)
        if data == "show-ring":
            print self.calc_optimal_ring_form(sock)
            self.user_input(sock)

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

    Thread(target=server.peer_discovery).start()
    Thread(target=server.ringo_server).start()
    #time.sleep(3)
    #Thread(target=server.user_input).start()


    # server = Server(FLAG, UDP_PORT, POC_NAME, POC_PORT, N)
    # client = Client(FLAG, UDP_PORT, POC_NAME, POC_PORT, N)
    #
    # server.start()
    # client.start()
    # server.join()
