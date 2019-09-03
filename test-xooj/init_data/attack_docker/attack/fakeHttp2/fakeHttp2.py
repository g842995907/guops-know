#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import requests
import random
import time

# url = "http://127.0.0.1"
cookie = {
    "CSRF":"EnPScmaWPfusXXZkxQILDNXGwgIihqYWyh5Ab7IybjvbD0GIENPHdwsE6s3OKhpi"
}
header = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
}   

TIMEOUT = 0.001
def monitor_get(url):
    
    try:
        requests.get(url, headers = header, cookies = cookie, timeout = TIMEOUT)
    except Exception as e:
        print("Get has happened")


def monitor_post(url, **kwargs):
    try:
        data = kwargs['data']
        # print("data ")
        requests.post(url, data, kwargs, timeout= TIMEOUT)
        
    except Exception as e:
        print("Post has happened")
        pass
        # time.sleep(1)


def login(url, username, password):
    login_url = url + "login/"
    # first, monitor get the login
    monitor_get(login_url)
    # and then , try to post url
    
    data = {
    "username":username,
    "password":password
    }
    # finally monitor logins
    monitor_post(login_url, data = data, cookies = cookie, headers = header)


def upload(url, image_name, image, image_group):
    upload_url = url + "upload/"
    files = {"file":(image_name, image, 'image/jpeg')}
    data = {
                "image_name":image_name,
        "image_groupe":image_group
    }
    # monitor_post(upload_url,data = data, files = files, headers = header)
    try:
        requests.post(upload_url, data = data, files = files, headers = header, timeout = TIMEOUT)
    except Exception as e:
        print("Send picture file")
        time.sleep(1)


def register(url, username, password):

    register_url = url + "register/"
    monitor_get(register_url)
    data = {
            "username":username,
            "password":password
    }
    monitor_post(register_url, data = data)


total_time = 20
usernames = ['HW','piggy','bertk','TKat','Robot','FAKing','Username','QwEaK','Test','Hakcking']    
passwords = ['6837605','tianxia512','wzj27713','19830307','793925564','chengkang','159648sl','a2135336','liudaqi','a26549828','tjl19820515','sn6331907','19851103','THW160178','k6r5c4yd','65627904','7187856','chen123','yyc1990']
pictures = ['test.jpg','logo.jpg','info.jpg','desktop.jpg','passwd.jpg']
pictures_group = ["NORMAL_IMAGE",'HACK_IMAGE']

def main_monitor(url):

    # first, try to register a new account
    index = random.randint(0, 30)
    username = usernames[index%len(usernames)]
    password = passwords[index%len(passwords)]

    register(url, username, password)
    # then, login it
    login(url, username, password)
    # if this is 7's ,upload a picture
    if index%7 == 0:
        fd = open("logo1.jpg",'rb')
        num = random.randint(0,10)
        upload(url, pictures[num%len(pictures)], fd, pictures_group[num%len(pictures_group)])
        fd.close()


def hack_monitor(url):

    username = "h4ck3r"
    password = "qw3edcft6"

    register(url, username, password)
    # then, login it
    login(url, username, password)
    # upload file 
    fd = open("logo1.jpg",'rb')
    upload(url, "logo1.jpg\x00.php", fd, "HACKIT")
    fd.close()
    print("Send HACK")


def attacker(host,port = 9998):
    url = "http://{}:{}/updateImage/"
    url = url.format(host, port)
    print(url)
    # login("testuser",123456)
    # img = open("logo1.jpg",'rb')
    # print("In here")
    # upload("test", img, "test_group")
    total_time = 10
    num = 0
    while True:
        num += 1
        if num == total_time:
            hack_monitor(url)
            break
            num = random.randint(0,10)
        else:
            main_monitor(url)
            time.sleep(1)
            
    return True


if __name__ == '__main__':
    attacker("127.0.0.1")
