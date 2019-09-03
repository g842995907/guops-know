#!/usr/bin/env bash

attack_type=$1
ips=$2
ports=$3


function udpflood(){
    cd attack/udpflood
    python udpflood.py $1 $2
}

function fakeCSRF(){
    cd attack/fakeCSRF
    python fakeCSRF.py $1 $2
}

while true
do

case $attack_type in
    "udpflood")
        udpflood $ips $ports
    ;;

    "fakeCSRF")
        fakeCSRF $ips $ports
    ;;

esac

cd /home
sleep 1s

done

