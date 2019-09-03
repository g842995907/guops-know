from __future__ import unicode_literals

import socket


local_ip = socket.gethostbyname(socket.gethostname())

redis_server = "controller"

redis_port = 6379

report_interval = 2

keep_history = 10
