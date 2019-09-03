# -*- coding: utf-8 -*-

import os
import re


def scan_file(dir, filename_str):
    name_pattern = re.compile(filename_str)
    files = []
    for filename in os.listdir(dir):
        if name_pattern.match(filename):
            filepath = os.path.join(dir, filename)
            filesize = os.path.getsize(filepath)
            files.append({
                'name': filename,
                'size': filesize,
            })
    return files