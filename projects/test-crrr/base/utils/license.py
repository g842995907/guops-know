# -*- coding: utf-8 -*-
import datetime
import os
import time
import commands
import re
import json
import logging
import fcntl

from django.core.cache import cache
from django.utils import timezone
from django.utils.translation import ugettext as _

from base.utils import x_rsa
from cr import settings
from system.models import SystemConfiguration

logger = logging.getLogger(__name__)


def judge_series_number(license_info):
    license_series_number = license_info.get("series_number", None)
    if license_series_number:
        series_number_file_path = os.path.join(settings.MEDIA_ROOT, 'harddisk')
        if not os.path.exists(series_number_file_path):
            os.mkdir(series_number_file_path)
        file_name = 'harddisk_info'
        full_file_name = os.path.join(series_number_file_path, file_name)
        if not os.path.exists(full_file_name):
            return False, _('x_disk_not_exist')
        with open(full_file_name) as fileobj:
            harddisk_series_number = fileobj.read().strip()
        if not harddisk_series_number == license_series_number:
            return False, _('x_disk_is_incorrect')
        return True, None
    else:
        return False, _('x_license_file_error')


def judge_time(license_info):
    deadline = license_info.get("deadline", None)
    if deadline:
        t = time.strptime(deadline, "%Y-%m-%d %H:%M:%S")
        y, m, d, h, M, s = t[0:6]
        deadline = datetime.datetime(y, m, d, h, M, s)

        deadline_time = SystemConfiguration.objects.filter(key='deadline_time').first()
        if deadline_time:
            deadline_time.value = deadline
            deadline_time.save()
        else:
            SystemConfiguration.objects.create(
                key='deadline_time',
                value=deadline
            )

        if deadline < timezone.now():
            return False, _('x_license_file_expired')
        return True, None
    else:
        return False, _('x_license_file_error')


def get_system_config(name):
    data = cache.get("_t_system_%s" % name)
    if data:
        return data

    sys_obj = SystemConfiguration.objects.filter(key=name).first()
    if sys_obj:
        data = sys_obj.value
        cache.set("_t_system_%s" % name, data, 60 * 60)
        return data

    return None


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


class BaseHardware(object):
    # 获取硬盘序号
    CMD_HD1 = "hdparm -I /dev/sda|grep 'Serial Number'|awk '{print $NF}'"
    CMD_HD2 = "ls -la /dev/disk/by-id/* |head -n1|awk '{print $(NF-2)}'|awk -F ':' '{print $NF}'"

    # 获取cpu ID
    CMD_CPU = "dmidecode -t 4 | grep ID | head -n 1 | awk -F ':' '{print $2}' | sed 's/ //g'"

    # 主板id
    CMD_MD = "dmidecode -t 2| grep 'Serial Number' | head -n 1 | awk -F ':' '{print $2}' | sed 's/ //g'"

    CMD_OK = 0

    def __init__(self):
        pass

    def get_hardware_info(self):
        return {
            'cpu': self.get_cpu_id(),
            'disk': self.get_disk_info(),
            'motherboard': self.get_motherboard_info(),
            'version': get_system_config('version') or get_version('system_configuration')
        }

    def get_cpu_id(self):
        return self._run_cmd(self.CMD_CPU)

    def get_disk_info(self):
        disk = self._run_cmd(self.CMD_HD1)
        if disk is None:
            disk = self._run_cmd(self.CMD_HD2)

        return disk

    def get_motherboard_info(self):
        return self._run_cmd(self.CMD_MD)

    def _run_cmd(self, cmd):
        status, output = commands.getstatusoutput(cmd)
        if status == self.CMD_OK:
            return output

        return None


class License(object):
    def __init__(self):
        self.private_key = os.path.join(settings.MEDIA_ROOT, "key/lic/key.pem")
        self.personal_license_path = os.path.join(settings.MEDIA_ROOT, 'personal_license')

    @staticmethod
    def genera_license_file(department):
        if department is None:
            return None

        filename = "{}-{}.lic".format(department.name, department.ip)
        license_path = os.path.join(settings.MEDIA_ROOT, 'tmp')

        if not os.path.exists(license_path):
            os.mkdir(license_path)

        # write license info
        full_file_name = os.path.join(license_path, filename)
        file_object = None

        try:
            file_object = open(full_file_name, 'w')
            file_object.write(department.license_info)
        except IOError as e:
            logger.error("write license error")
            return None
        finally:
            if file_object:
                file_object.close()

        # make license file
        encrypt_path = os.path.join(settings.MEDIA_ROOT, 'license')
        if not os.path.exists(encrypt_path):
            os.mkdir(encrypt_path)

        encrypt_file_name = "{}-{}.encrypt".format(department.name, department.ip)
        encrypt_full_path = os.path.join(encrypt_path, encrypt_file_name)
        if os.path.exists(encrypt_full_path):
            os.remove(encrypt_full_path)

        # encrypt file and zip
        try:
            lic_public_key_path = os.path.join(settings.MEDIA_ROOT, 'key/lic/key_pub.pem')
            x_rsa.x_encrypt(full_file_name, encrypt_full_path, lic_public_key_path)
        except Exception as e:
            logger.error("encrypt error department[%s] msg[%s]", department.name, str(e))
            return None

        return encrypt_full_path

    def get_license_info(self, license_path):
        if not license_path or not os.path.exists(license_path):
            logger.error('license file not exist')
            return None

        decrypt_file_name = "decrypt.lic"
        decrypt_full_path = os.path.join(self.personal_license_path, decrypt_file_name)

        try:
            x_rsa.x_decrypt(license_path, decrypt_full_path, self.private_key)
        except ValueError as e:
            logger.error('private key error')
            return None

        _license = None
        with open(decrypt_full_path, 'r') as file_obj:
            fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)
            _license = file_obj.read()

        # 大并发下，read可能会失败，一直定位不到问题
        if _license is None or len(_license) == 0:
            with open(decrypt_full_path, 'r') as file_obj:
                fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)
                _license = file_obj.read()
        try:
            license_info = json.loads(_license)
        except Exception as e:
            raise e

        return license_info

    def handle_config(self, license_info, license_name, sysconfig_name):
        value = license_info.get(license_name, None)

        if value is not None:
            system_configuration = SystemConfiguration.objects.filter(key=sysconfig_name)
            if system_configuration:
                s_c = system_configuration.first()
                s_c.value = value
                s_c.save()
            else:
                SystemConfiguration.objects.create(key=sysconfig_name, value=value)

        return value

    def validate_license(self, s, c, m, v):
        bhw = BaseHardware()
        hard_info = bhw.get_hardware_info()

        if hard_info.get("cpu") != c or hard_info.get("disk") != s or hard_info.get("motherboard") != m \
                or hard_info.get("version") != v:
            return False

        return True

    def judge_authorize(self, license_path):
        license_info = self.get_license_info(license_path)
        if not license_info:
            return 1, "validate error"

        logger.debug("license [%s]", license_info)
        self.handle_config(license_info, "concurrent", "all_env_count")
        self.handle_config(license_info, "terminal_node_number", "terminal_node_number")
        self.handle_config(license_info, "edition", "edition")
        self.handle_config(license_info, "trial", "trial")
        deadline = self.handle_config(license_info, "deadline", "deadline_time")

        series_number = license_info.get("series_number", None)
        cpu = license_info.get("cpu", None)
        motherboard = license_info.get("motherboard", None)
        version = get_system_config('version') or get_version('system_configuration')

        if not deadline or deadline == "":
            logger.error("validate error, deadline null")
            return 1, "deadline error"

        try:
            t = time.strptime(deadline, "%Y-%m-%d %H:%M:%S")
            y, m, d, h, M, s = t[0:6]
            deadline = datetime.datetime(y, m, d, h, M, s)
        except Exception:
            logger.error("validate error, deadline error")
            return 1, "deadline error"

        if deadline < timezone.now():
            return 1, _('x_license_file_expired')

        ret = self.validate_license(series_number, cpu, motherboard, version)
        if ret:
            return 0, None

        return 1, "validate error"


class LicenseInfo(object):
    def __init__(self):
        pass

    def get_encrypt_info(self):
        dict_base_info = BaseHardware().get_hardware_info()

        # dict ==> string
        try:
            string_base_info = json.dumps(dict_base_info)
        except Exception as e:
            logger.error("json dump error dict_info[%s] msg[%s]", dict_base_info, str(e))
            return None

        try:
            # string ->encrypt
            # rsa encrypt with info public key
            info_public_file_path = os.path.join(settings.MEDIA_ROOT, 'key/info/key_pub.pem')
            encrypt_info = x_rsa.rsa_encrypt(info_public_file_path, string_base_info)

            # string -> hex
            hex_encrypt_info = encrypt_info.encode('hex')

            return hex_encrypt_info
        except Exception as e:
            logger.error("get license encrypt info error msg[%s]", str(e))
            return None
