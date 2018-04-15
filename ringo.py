import socket
import sys
import os

from threading import Thread
import threading
import time
import packet

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
        self.filename = ""
        self.running = True
        self.alive_vector = []
        self.blast_running = True
        self.dead_ringo = []
        self.rtt_vec_check = False
        self.ka_on = False
        self.pack_seq = 0
        self.ack_seq = 0
        self.data_send_block = False
        self.send_packet = packet.create_packet("","","","","","")

    def ringo_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', self.udp_port))
        #sock.settimeout(2.0)

        while True:
            while self.running:
                data, address = sock.recvfrom(BUFFER_SIZE)
                #print data
                if not data:
                    continue

                d = packet.deconstruct_packet(packet.bytes_to_packet(data))
                #print d
                if d[0].split("%")[4] == "KA":
                    p = packet.create_packet(self.udp_port, address[1], self.pack_seq, self.ack_seq, "KAACK", "")
                    sock.sendto(packet.packet_to_bytes(p), address)

                if d[0].split("%")[4] == "KAACK":
                    if address not in self.alive_vector:
                        self.alive_vector.append(address)

                if d[0].split("%")[4] == "PD":
                    self.peer_discovery_append(d[1].split(";")[0].split(",")[0], d[1].split(";")[0].split(",")[1])
                    if len(self.ringo_vector) != self.n and self.pd_done == 0:
                        #self.blast_running = True
                        sender = threading.Thread(target=self.peer_discover_blast, args=(sock,))
                        sender.daemon = True
                        sender.start()

                if len(self.ringo_vector) == self.n and self.pd_done == 0:
                    self.pd_done = 1
                    final_vector = ""
                    for r in self.ringo_vector:
                        final_vector += r[0] + "," + str(r[1]) + ";"

                    for r in self.ringo_vector:
                        if r != (socket.gethostbyname(socket.gethostname()), int(self.udp_port)):
                            p = packet.create_packet(self.udp_port, r[1], self.pack_seq, self.ack_seq, "PDDONE", final_vector)
                            sock.sendto(packet.packet_to_bytes(p), r)

                    self.blast_running = False

                if d[0].split("%")[4] == "PDDONE":
                    for da in d[1].split(";")[0:len(d[1].split(";"))-1]:
                        ringo_check = (da.split(",")[0], int(da.split(",")[1]))
                        if ringo_check not in self.ringo_vector:
                            self.ringo_vector.append(ringo_check)

                    for r in self.ringo_vector:
                        #if r != (socket.gethostbyname(socket.gethostname()), int(self.udp_port)):
                        p = packet.create_packet(self.udp_port, r[1], self.pack_seq, self.ack_seq, "FLAG", "")
                        sock.sendto(packet.packet_to_bytes(p), r)

                    rtt = threading.Thread(target=self.ringo_rtt_loop, args=(sock,))
                    rtt.daemon = True
                    rtt.start()

                if d[0].split("%")[4] == "PDUP":
                    for da in d[1].split(";")[0:len(d[1].split(";"))-1]:
                        ringo_check = (da.split(",")[0], int(da.split(",")[1]))
                        if ringo_check not in self.ringo_vector:
                            self.peer_discovery_append(da.split(",")[0], da.split(",")[1])

                if d[0].split("%")[4] == "RTTSEND":
                    p = packet.create_packet(self.udp_port, address[1], self.pack_seq, self.ack_seq, "RTTREC", d[1])
                    sock.sendto(packet.packet_to_bytes(p), address)

                if d[0].split("%")[4] == "RTTREC":
                    self.rtt_recv(time.time(), d[1], address, sock)

                if d[0].split("%")[4] == "RTTVEC":
                    self.add_vec_to_matrix(d[1], sock)

                if d[0].split("%")[4] == "RTTDONE":
                    self.sync_matrix(d[1])
                    time.sleep(5)

                    if self.ka_on == False:
                        input_thread = threading.Thread(target=self.user_input, args=(sock,))
                        input_thread.daemon = True
                        input_thread.start()
                        ka_thread = threading.Thread(target=self.ka, args=(sock,))
                        ka_thread.daemon = True
                        ka_thread.start()

                if d[0].split("%")[4] == "FLAG":
                    p = packet.create_packet(self.udp_port, address[1], self.pack_seq, self.ack_seq, "RECFLAG", self.flag)
                    sock.sendto(packet.packet_to_bytes(p), address)

                if d[0].split("%")[4] == "RECFLAG":
                    self.flag_dic[address] = d[1]

                if d[0].split("%")[4] == "FILE":
                    if self.flag == "R":
                        new_filename = d[1].split(".")[0] + "_new" + "." + d[1].split(".")[1]
                        self.filename = new_filename
                        p = packet.create_packet(self.udp_port, address[1], d[0].split("%")[2], d[0].split("%")[3], "DACK", "")
                        sock.sendto(packet.packet_to_bytes(p), address)
                    else:
                        self.data_rec(d, sock, address)

                if d[0].split("%")[4] == "DSEND" or d[0].split("%")[4] == "DDONE":
                    if self.flag == "R":
                        if d[0].split("%")[4] != "DDONE":
                            self.data_done(d, sock, address)
                        else:
                            p = packet.create_packet(self.udp_port, address[1], d[0].split("%")[2], d[0].split("%")[3], "DDONEACK", "")
                            sock.sendto(packet.packet_to_bytes(p), address)
                    else:
                        if d[0].split("%")[4] == "DDONE":
                            self.data_rec_done(d, sock, address)
                        else:
                            self.data_rec(d, sock, address)

                if d[0].split("%")[4] == "DACK":
                    check_pack_num = d[0].split("%")[2]
                    check_ack_num = d[0].split("%")[3]
                    #print self.pack_seq
                    #print self.ack_seq
                    if int(check_pack_num) == self.pack_seq and int(check_ack_num) == self.ack_seq:
                        #print "Received the correct packet ack"
                        self.pack_seq += 1
                        if self.ack_seq == 0:
                            self.ack_seq = 1
                        else:
                            self.ack_seq = 0

                        self.data_send_block = True
                    else:
                        sock.sendto(packet.packet_to_bytes(self.send_packet), address)
                        #NEED TO RESEND
                        #Need to implement timeout time

                if d[0].split("%")[4] == "DDONEACK":
                    self.data_send_block = False

                if d[0].split("%")[4] == "PDREV":
                    for da in d[1].split(";")[0:len(d[1].split(";"))-1]:
                        ringo_check = (da.split(",")[0], int(da.split(",")[1]))
                        if ringo_check not in self.ringo_vector:
                            self.ringo_vector.append(ringo_check)

                    for r in self.ringo_vector:
                        #if r != (socket.gethostbyname(socket.gethostname()), int(self.udp_port)):
                        p = packet.create_packet(self.udp_port, r[1], self.pack_seq, self.ack_seq, "FLAG", "")
                        sock.sendto(packet.packet_to_bytes(p), r)

                    self.pd_done = 1
                    self.cur_other_ringo_count = self.n - 1
                    pack = packet.create_packet(self.udp_port, address[1], self.pack_seq, self.ack_seq, "PDREVDONE", "")
                    sock.sendto(packet.packet_to_bytes(pack), address)

                if d[0].split("%")[4] == "RTTREDO":
                    self.rtt_vector = []
                    self.rtt_matrix = []
                    self.rtt_vec_check = False
                    rtt = threading.Thread(target=self.ringo_rtt_loop, args=(sock,))
                    rtt.daemon = True
                    rtt.start()

                if d[0].split("%")[4] == "PDREVDONE":
                    for r in self.ringo_vector:
                        p = packet.create_packet(self.udp_port, r[1], self.pack_seq, self.ack_seq, "RTTREDO", "")
                        sock.sendto(packet.packet_to_bytes(p), r)

    def peer_discovery(self):
        self.blast_running = True
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('',0))
        self.ringo_vector.append((socket.gethostbyname(socket.gethostname()), self.udp_port))

        if self.poc_name != "0" and self.poc_port != 0:
            self.peer_discovery_append(socket.gethostbyname(self.poc_name), self.poc_port)

        while self.cur_other_ringo_count < self.n and self.blast_running == True:
            pdPacket = ""
            for r in self.ringo_vector:
                pdPacket += r[0] + "," + str(r[1]) + ";"

            for r in self.ringo_vector:
                if r != (socket.gethostbyname(socket.gethostname()), self.udp_port):
                    p = packet.create_packet(self.udp_port, r[1], self.pack_seq, self.ack_seq, "PD", pdPacket)
                    sock.sendto(packet.packet_to_bytes(p), r)
                    time.sleep(1)

    def peer_discovery_append(self, client_address, server_port):
        new_ringo = (client_address, int(server_port))
        if new_ringo not in self.ringo_vector:
            self.ringo_vector.append(new_ringo)
            self.cur_other_ringo_count += 1

    def peer_discover_blast(self, sock):
        while self.blast_running:
            update_vector = ""
            for r in self.ringo_vector:
                update_vector += r[0] + "," + str(r[1]) + ";"

            for r in self.ringo_vector:
                if r != (socket.gethostbyname(socket.gethostname()), int(self.udp_port)):
                    p = packet.create_packet(self.udp_port, r[1], self.pack_seq, self.ack_seq, "PDUP", update_vector)
                    sock.sendto(packet.packet_to_bytes(p), r)

    def rtt_calc(self, dest, sock):
        # initial time when sent
        initialTime = time.time()
        p = packet.create_packet(self.udp_port, dest[1], self.pack_seq, self.ack_seq, "RTTSEND", str(initialTime))
        sock.sendto(packet.packet_to_bytes(p), dest)

    def rtt_recv(self, final, initial, address, sock):
        my_t = ((socket.gethostbyname(socket.gethostname()), int(self.udp_port)), (socket.gethostbyname(socket.gethostname()), int(self.udp_port)), 0.0)
        if my_t not in self.rtt_vector:
            self.rtt_vector.append(my_t)

        t = ((socket.gethostbyname(socket.gethostname()), int(self.udp_port)), address, final - float(initial))
        rtt_vec_check = True

        for v in self.rtt_vector:
            if t[0] == v[0] and t[1] == v[1]:
                rtt_vec_check = False

        if rtt_vec_check == True:
            self.rtt_vector.append(t)

        if len(self.rtt_vector) == self.n and self.rtt_vec_check == False:
            self.rtt_vec_check = True
            for rtt in self.rtt_vector:
                t_add = (rtt[0], rtt[1], rtt[2])
                if t_add not in self.rtt_matrix:
                    self.rtt_matrix.append(t_add)

            send_vec = ""
            for rtt in self.rtt_vector:
                send_vec += str(rtt[0][0]) + "," + str(rtt[0][1]) + "," + str(rtt[1][0]) + "," + str(rtt[1][1]) + "," + str(rtt[2]) + ";"

            for r in self.ringo_vector:
                if r != (socket.gethostbyname(socket.gethostname()), int(self.udp_port)):
                    p = packet.create_packet(self.udp_port, r[1], self.pack_seq, self.ack_seq, "RTTVEC", send_vec)
                    sock.sendto(packet.packet_to_bytes(p), r)

    def add_vec_to_matrix(self, data, sock):
        for d in data.split(";")[0:len(data.split(";"))-1]:
            t = ((d.split(",")[0], int(d.split(",")[1])), (d.split(",")[2], int(d.split(",")[3])), float(d.split(",")[4]))
            if t not in self.rtt_matrix:
                self.rtt_matrix.append(t)

        if len(self.rtt_matrix) == self.n * self.n and self.poc_name == "0" and self.poc_port == 0:
            time.sleep(2)
            send_matrix = ""
            for rtt in self.rtt_matrix:
                send_matrix += str(rtt[0][0]) + "," + str(rtt[0][1]) + "," + str(rtt[1][0]) + "," + str(rtt[1][1]) + "," + str(rtt[2]) + ";"

            for r in self.ringo_vector:
                p = packet.create_packet(self.udp_port, r[1], self.pack_seq, self.ack_seq, "RTTDONE", send_matrix)
                sock.sendto(packet.packet_to_bytes(p), r)

    def ringo_rtt_loop(self, sock):
        for r in self.ringo_vector:
            if r != (socket.gethostbyname(socket.gethostname()), int(self.udp_port)):
                self.rtt_calc(r, sock)

    def sync_matrix(self, data):
        self.rtt_matrix = []
        for d in data.split(";")[0:len(data.split(";"))-1]:
            t = ((d.split(",")[0], int(d.split(",")[1])), (d.split(",")[2], int(d.split(",")[3])), float(d.split(",")[4]))
            if t not in self.rtt_matrix:
                self.rtt_matrix.append(t)

    def find_all_paths(self, matrix, start, end, path=[]):
        path = path + [start]
        if start == end:
            return [path]

        paths = []
        for x in matrix:
            if x[0][1] == start:
                if x[1][1] not in path:
                    newpaths = self.find_all_paths(matrix, x[1][1], end, path)
                    for newpath in newpaths:
                        paths.append(newpath)

        return paths

    def calc_optimal_ring_form(self, sock):
        starter = []
        forwarder = []
        final = []

        for key, value in self.flag_dic.iteritems():
            if value == 'S':
                starter = key
            elif value == 'F':
                if self.dead_ringo:
                    if self.dead_ringo != key:
                        forwarder.append(key)
                else:
                    forwarder.append(key)
            else:
                final = key

        small = []
        if len(forwarder) == 0:
            small.append(starter)
            small.append(final)
        elif len(forwarder) == 1:
            small.append(starter)
            small.append(forwarder[0])
            small.append(final)
        else:
            starting_list = []
            for rtt in self.rtt_matrix:
                if rtt[0][1] == starter[-1] and rtt[1][1] != starter[-1]:
                    starting_list.append(rtt[1][1])

            rtt_without_start = []
            for x in self.rtt_matrix:
                if x[0][1] != starter[-1]:
                    if self.dead_ringo:
                        if self.dead_ringo != x[0] and self.dead_ringo != x[1]:
                            rtt_without_start.append(x)
                    else:
                        rtt_without_start.append(x)

            all_paths = [[[starter[-1]]+y for y in self.find_all_paths(rtt_without_start,x,final[-1])] for x in starting_list]
            test_paths = []
            for x in all_paths:
                for y in x:
                    if not self.dead_ringo:
                        if len(y) == self.n:
                            test_paths.append(y)
                    else:
                        if len(y) == self.n - 1:
                            test_paths.append(y)

            lowest_cost = 9999999
            lowest_path = []
            for t in test_paths:
                cur_cost = 0
                for r in self.rtt_matrix:
                    for i in range(len(t) - 1):
                        if r[0][1] == t[i] and r[1][1] == t[i + 1]:
                            cur_cost += r[2]
                if cur_cost < lowest_cost:
                    lowest_cost = cur_cost
                    lowest_path = t
            small = lowest_path

            for i, s in enumerate(small):
                for r in self.ringo_vector:
                    if r[1] == s:
                        small[i] = r
                        break

        return small

    def send_data(self, filename, sock):
        travel_path = self.calc_optimal_ring_form(sock)
        p = packet.create_packet(self.udp_port, travel_path[1][1], self.pack_seq, self.ack_seq, "FILE", filename)
        sock.sendto(packet.packet_to_bytes(p), travel_path[1])
        f = open(filename,"rb")
        send_data = f.read(512)

        while send_data:
            if self.data_send_block:
                p = packet.create_packet(self.udp_port, travel_path[1][1], self.pack_seq, self.ack_seq, "DSEND", send_data)
                self.send_packet = p
                sock.sendto(packet.packet_to_bytes(self.send_packet), travel_path[1])
                send_data = f.read(512)
                self.data_send_block = False

        p = packet.create_packet(self.udp_port, travel_path[1][1], self.pack_seq, self.ack_seq, "DDONE", "")
        sock.sendto(packet.packet_to_bytes(p), travel_path[1])

    def data_rec(self, d, sock, address):
        travel_path = self.calc_optimal_ring_form(sock)
        i = 0
        for x in travel_path:
            if x[1] == self.udp_port:
                i += 1
                break
            i += 1

        p = packet.create_packet(self.udp_port, address[1], d[0].split("%")[2], d[0].split("%")[3], "DACK", "")
        sock.sendto(packet.packet_to_bytes(p), address)
        data_carry = packet.create_packet(self.udp_port, travel_path[i][1], self.pack_seq, self.ack_seq, d[0].split("%")[4], d[1])
        sock.sendto(packet.packet_to_bytes(data_carry), travel_path[i])

    def data_rec_done(self, d, sock, address):
        travel_path = self.calc_optimal_ring_form(sock)
        i = 0
        for x in travel_path:
            if x[1] == self.udp_port:
                i += 1
                break
            i += 1

        p = packet.create_packet(self.udp_port, address[1], d[0].split("%")[2], d[0].split("%")[3], "DDONEACK", "")
        sock.sendto(packet.packet_to_bytes(p), address)
        data_carry = packet.create_packet(self.udp_port, travel_path[i][1], d[0].split("%")[2], d[0].split("%")[3], d[0].split("%")[4], d[1])
        sock.sendto(packet.packet_to_bytes(data_carry), travel_path[i])

    def data_done(self, d, sock, address):
        p = packet.create_packet(self.udp_port, address[1], d[0].split("%")[2], d[0].split("%")[3], "DACK", "")
        sock.sendto(packet.packet_to_bytes(p), address)
        data_write = d[1]
        with open(self.filename, 'ab') as f:
            f.write(data_write)

    def ka(self, sock):
        self.ka_on = True
        while True:
            while self.running:
                for r in self.ringo_vector:
                    if r != (socket.gethostbyname(socket.gethostname()), int(self.udp_port)):
                        p = packet.create_packet(self.udp_port, r[1], self.pack_seq, self.ack_seq, "KA", "")
                        sock.sendto(packet.packet_to_bytes(p), r)
                time.sleep(3)
                #print self.alive_vector
                if len(self.alive_vector) != self.n - 1:
                    #print "KEEP ALIVE NOT GOOD"
                    for r in self.ringo_vector:
                        if r not in self.alive_vector:
                            self.dead_ringo = r
                    if self.flag == "R":
                        revive_vector = ""
                        for r in self.ringo_vector:
                            revive_vector += r[0] + "," + str(r[1]) + ";"
                        p = packet.create_packet(self.udp_port, self.dead_ringo[1], self.pack_seq, self.ack_seq, "PDREV", revive_vector)
                        sock.sendto(packet.packet_to_bytes(p), self.dead_ringo)

                else:
                    self.dead_ringo = []
                self.alive_vector = []

    def go_offline(self, t, sock):
        self.running = False
        time.sleep(float(t))
        #print "Done sleeping"
        self.ringo_vector = []
        self.pd_done = 0
        self.cur_other_ringo_count = 0
        self.rtt_vector = []
        self.rtt_matrix = []
        self.flag_dic = {}
        self.filename = ""
        self.running = True
        self.alive_vector = []
        self.blast_running = False
        self.dead_ringo = []
        self.rtt_vec_check = False
        self.ka_on = True
        self.pack_seq = 0
        self.ack_seq = 0
        self.data_send_block = False
        self.send_packet = packet.create_packet("","","","","","")

    def disconnect(self, sock):
        self.running = False
        sock.close()
        os._exit(0)

    def user_input(self, sock):
        data = raw_input('> ')
        if data == "show-matrix":
            print self.rtt_matrix
            self.user_input(sock)
        if data == "show-ring":
            print self.calc_optimal_ring_form(sock)
            self.user_input(sock)
        if data.split(" ")[0] == "send" and self.flag == "S":
            filename = data.split(" ")[1]
            self.send_data(filename, sock)
            self.user_input(sock)
        if data.split(" ")[0] == "offline" and self.flag == "F":
            t = data.split(" ")[1]
            self.go_offline(t, sock)
            self.user_input(sock)
        if data.split(" ")[0] == "disconnect":
            self.disconnect(sock)
        else:
            print "That statement does not work at this moment or you do not have the correct flag to complete that task. The only commands that work are show-matrix, show-ring, offline, and send. Only Forwarders can go offline and only the Sender can send. Please try again"
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
    if sys.argv[1] != "F" and sys.argv[1] != "S" and sys.argv[1] != "R":
        print "You can only enter the flag as S, R, or F"
        sys.exit(1)
    if int(sys.argv[5]) < 1:
        print "Your number of ringos entered is too small. Please pick a higher value"
        sys.exit(1)

    FLAG = sys.argv[1]
    UDP_PORT = 50000
    if int(sys.argv[2]) > 49152 and int(sys.argv[2]) < 65535:
        UDP_PORT = int(sys.argv[2])
    BUFFER_SIZE = 2048
    POC_NAME = sys.argv[3]
    POC_PORT = int(sys.argv[4])
    N = int(sys.argv[5])
    # p = packet.create_packet(56789, 12345, 5, 10, "n", 200, "heyyyyy yall")
    # x = packet.packet_to_bytes(p)
    # print x
    # y = packet.bytes_to_packet(x)
    # print y
    # print packet.deconstruct_packet(y)
    #print socket.gethostname()

    server = Server(FLAG, UDP_PORT, POC_NAME, POC_PORT, N)

    Thread(target=server.peer_discovery).start()
    Thread(target=server.ringo_server).start()
