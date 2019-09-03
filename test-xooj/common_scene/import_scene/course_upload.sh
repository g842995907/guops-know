#!/usr/bin/env bash

echo "[+] Start upload: $1"

echo "remote execute :  course_convert.sh $*"
fab -u root -p XXXXXX -H 10.10.62.252 -- "cd /root/course_import && /bin/bash course_convert.sh $*"

echo "************************"
echo "Done"
echo "************************"
