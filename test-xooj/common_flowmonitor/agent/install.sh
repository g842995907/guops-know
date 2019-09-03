#!/usr/bin/env bash

yum install -y epel-release
yum install -y redis
sed -i 's/bind 127.0.0.1/bind 0.0.0.0/' /etc/redis.conf
systemctl enable redis
systemctl start redis
yum install -y gcc

cp -rf ../../common_flowmonitor /usr/lib/python2.7/site-packages/
yum install -y libvirt-devel

mkdir ~/.pip/
cat <<EOF >> ~/.pip/pip.conf
[global]
index-url = http://mirrors.aliyun.com/pypi/simple/

[install]
trusted-host=mirrors.aliyun.com
EOF
pip install -r ../requirements.txt

# !!! Not work !!!
#
#cat << EOF > /usr/lib/systemd/system/cp-net-flow-agent.service
#[Unit]
#Description=Network Flow Agent
#After=syslog.target network.target libvirtd.service
#
#[Service]
#Type=notify
#NotifyAccess=all
#TimeoutStartSec=0
#Restart=always
#User=root
#ExecStart=/usr/bin/python /usr/lib/python2.7/site-packages/common_flowmonitor/agent/net_flow_agent.py start
#
#[Install]
#WantedBy=multi-user.target
#EOF
#
#chmod 644 /usr/lib/systemd/system/cp-net-flow-agent.service
#systemctl enable cp-net-flow-agent


cat << EOF > /usr/lib/systemd/system/cp-net-flow-server.service
[Unit]
Description=Network Flow Agent
After=syslog.target network.target libvirtd.service

[Service]
Type=notify
NotifyAccess=all
TimeoutStartSec=0
Restart=always
User=root
ExecStart=/usr/bin/python /usr/lib/python2.7/site-packages/common_flowmonitor/server/net_flow_server.py start

[Install]
WantedBy=multi-user.target
EOF

chmod 644 /usr/lib/systemd/system/cp-net-flow-server.service
systemctl enable cp-net-flow-server
