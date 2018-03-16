import threading from Thread
import np from numpy

import socket
import sys
import time
import requests

class Connection:
    def __init__(self, remote_ip, remote_port):
        self.ip = remote_ip
        self.port = remote_port
        self.socket = socket.socket(family=AF_INET, type=SOCK_DGRAM)
        self.socket.bind(self.ip)

    def incoming(self, msg):




    def outgoing(self, msg):


