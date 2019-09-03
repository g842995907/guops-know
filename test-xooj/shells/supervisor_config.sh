# 配置nginx,memcached supervisor
touch /etc/supervisord.d/service.conf
cat <<"EOF" > /etc/supervisord.d/service.conf
[program:nginx]
command=/usr/local/nginx/sbin/nginx -c /usr/local/nginx/conf/xoj.conf
autostart=true
autorestart=true
user=root

[program:memcached]
command=memcached -uroot -l127.0.0.1
autostart=true
autorestart=true
user=root

[program:redis]
command=redis-server
autostart=true
autorestart=true
user=root
EOF

# 配置xoj supervisor
touch /etc/supervisord.d/xoj.conf
cat <<"EOF" > /etc/supervisord.d/xoj.conf
[program:xoj]
command=/root/.virtualenvs/xoj/bin/gunicorn oj.wsgi -c gunicorn_config.py
directory=/home/x-oj/
autostart=true
autorestart=true
user=root


[program:check_create_pool]
command=/root/.virtualenvs/xoj/bin/python manage.py check_create_pool
directory=/home/x-oj/
autostart=true
autorestart=true
user=root

[program:AD_daphne]
command=/root/.virtualenvs/xoj/bin/daphne oj.asgi:channel_layer -b 127.0.0.1 -p 8088
directory=/home/x-oj/
autostart=true
autorestart=true
user=root

[program:AD_runworker]
command=/root/.virtualenvs/xoj/bin/python manage.py runworker
directory=/home/x-oj/
numprocs=4
process_name=%(program_name)s_%(process_num)02d
autostart=true
autorestart=true
user=root

[program:AD_rundelay]
command=/root/.virtualenvs/xoj/bin/python manage.py rundelay
directory=/home/x-oj/
autostart=true
autorestart=true
user=root

[program:monitor_system_status]
command=/root/.virtualenvs/xoj/bin/python manage.py monitor_system_status
directory=/home/x-oj/
autostart=true
autorestart=true
user=root

EOF
