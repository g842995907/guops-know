#!/usr/bin/env bash

echo "[+] Start upload: $1"

echo "remote execute :  exam_convert.sh $*"
fab -u root -p XXXXXX -H 10.10.62.252 -- "cd /root/exam_import && /bin/bash exam_convert.sh $*"

echo "************************"
echo "Done"
echo "************************"
