# -*- coding: utf-8 -*-
import hashlib
import uuid

def generate_unique_key():
    return str(uuid.uuid4())

fixed_delete_flag = hashlib.md5('xoj').hexdigest()
# 删除标记, 附加到记录唯一字段，避免删除记录占用唯一资源
def generate_delete_flag(fixed=True):
    if fixed:
        return ':%s' % fixed_delete_flag
    return ':%s' % generate_unique_key()