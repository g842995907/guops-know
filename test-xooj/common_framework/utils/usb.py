# -*- coding: utf-8 -*-

import logging
import os
import subprocess

from common_framework.utils.unique import generate_unique_key


logger = logging.getLogger(__name__)


def get_usb_devices():
    usb_devices = []
    with open("/proc/partitions") as partitionsFile:
        lines = partitionsFile.readlines()[2:]
        for line in lines:
            words = [x.strip() for x in line.split()]
            minorNumber = int(words[1])
            deviceName = words[3]
            if minorNumber % 16 == 0:
                path = "/sys/class/block/" + deviceName
                if os.path.islink(path):
                    if os.path.realpath(path).find("/usb") > 0:
                        usb_devices.append("/dev/%s" % deviceName)
    return usb_devices


def mount_device(device):
    key = generate_unique_key()
    mount_path = '/mnt/%s' % key
    mount_cmd = 'mount %s %s' % (device, mount_path)
    logger.info(mount_cmd)
    os.makedirs(mount_path)
    subprocess.call(mount_cmd, shell=True)
    return mount_path


def umount_device(mount_path):
    umount_cmd = 'umount %s' % mount_path
    logger.info(umount_cmd)
    subprocess.call(umount_cmd, shell=True)
    os.removedirs(mount_path)


class usb(object):

    def __enter__(self):
        usb_devices = get_usb_devices()
        self.mount_paths = []
        for usb_device in usb_devices:
            mount_path = mount_device(usb_device)
            self.mount_paths.append(mount_path)
        return self.mount_paths

    def __exit__(self, exc_type, exc_val, exc_tb):
        for mount_path in self.mount_paths:
            umount_device(mount_path)

