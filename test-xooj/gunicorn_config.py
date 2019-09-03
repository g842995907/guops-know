import multiprocessing

bind = '127.0.0.1:8077'
worker_class = 'gevent'
workers = 16
daemon = False
timeout = 3600

loglevel = 'info'
errorlog = './log/error.log'
accesslog = './log/access.log'
