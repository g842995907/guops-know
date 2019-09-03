import hashlib
import os

import time


def timestamp_to_time(timestamp):
    timeStruct = time.localtime(timestamp)
    return time.strftime('%Y-%m-%d %H:%M:%S', timeStruct)


def get_file_size(filePath):
    filePath = unicode(filePath, 'utf8')
    fsize = os.path.getsize(filePath)
    fsize = fsize / float(1024 * 1024)
    return round(fsize, 2)


def get_file_create_time(filePath):
    filePath = unicode(filePath, 'utf8')
    t = os.path.getctime(filePath)
    return timestamp_to_time(t)


def get_file_modify_time(filePath):
    filePath = unicode(filePath, 'utf8')
    t = os.path.getmtime(filePath)
    return timestamp_to_time(t)

def get_md5(file_path):
  md5 = None
  if os.path.isfile(file_path):
    f = open(file_path,'rb')
    md5_obj = hashlib.md5()
    md5_obj.update(f.read())
    hash_code = md5_obj.hexdigest()
    f.close()
    md5 = str(hash_code).lower()
  return md5