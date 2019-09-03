# -*- coding: utf-8 -*-
import json
import logging
import os
import uuid

from django.conf import settings
from django.utils import six
from django.templatetags.static import static

from common_framework.utils.enum import enum
from common_framework.utils.text import contain_zh

from common_env.models import StandardDevice
from common_env.setting import api_settings

from .exceptions import MsgException
from .error import error


windows_spliter = '''\r
'''

linux_spliter = '''
'''


window_template = enum(
    BASE_DIR='''\r
mkdir {base_dir}\r
mkdir {base_dir}\\custom_install\r
''',
    CUSTOM_NORMAL_INSTALL='''\r
cd {base_dir}\r
{install_script}\r
''',
    CUSTOM_INSTALL='''\r
mkdir {base_dir}\\custom_install\\{installer_folder}\r
winrar x -y "{file_path}" "{base_dir}\\custom_install\\{installer_folder}"\r
call "{base_dir}\\custom_install\\{installer_folder}\\{install_script}"\r
''',
    MADE_SCRIPT_INSTALL='''\r
curl -o "{base_dir}\\custom_install\\install.bat" {file_url}\r
call "{base_dir}\\custom_install\\install.bat"\r
''',
)

linux_template = enum(
    BASE_DIR='''
mkdir {base_dir}
mkdir {base_dir}/custom_install
''',
    CUSTOM_NORMAL_INSTALL='''
cd {base_dir}
{install_script}
''',
    CUSTOM_INSTALL='''
mkdir {base_dir}/custom_install/{installer_folder}
unzip {file_path} -d {base_dir}/custom_install/{installer_folder}
cd {base_dir}/custom_install/{installer_folder}
chmod +x {base_dir}/custom_install/{installer_folder}/*.sh
/bin/bash {base_dir}/custom_install/{installer_folder}/{install_script}
sync
''',
)


def get_spliter(system_sub_type):
    system_type = StandardDevice.SystemSubTypeMap[system_sub_type]
    if system_type == StandardDevice.SystemType.WINDOWS:
        return windows_spliter
    else:
        return linux_spliter


def generate_base_dir_script(system_sub_type):
    system_type = StandardDevice.SystemSubTypeMap[system_sub_type]
    if system_type == StandardDevice.SystemType.WINDOWS:
        script = window_template.BASE_DIR.format(
            base_dir=api_settings.WINDOWS_BASE_DIR,
        )
    else:
        script = linux_template.BASE_DIR.format(
            base_dir=api_settings.LINUX_BASE_DIR,
        )
    return script


def generate_file_download_script(file_url, system_sub_type, file_name=None):
    if not file_name:
        file_name = file_url.split('/')[-1]
    system_type = StandardDevice.SystemSubTypeMap[system_sub_type]
    if system_type == StandardDevice.SystemType.WINDOWS:
        file_path = r'{base_dir}\{file_name}'.format(
            base_dir=api_settings.WINDOWS_BASE_DIR,
            file_name=file_name,
        )
    else:
        file_path = r'{base_dir}/{file_name}'.format(
            base_dir=api_settings.LINUX_BASE_DIR,
            file_name=file_name,
        )
    script = r'curl -o "{file_path}" {file_url}'.format(
        file_path=file_path,
        file_url=file_url,
    )
    return file_path, script


def generate_default_install_script(file_path, system_sub_type):
    script = ''
    if system_sub_type  in (
        StandardDevice.SystemSubType.WINDOWS_10,
        StandardDevice.SystemSubType.WINDOWS_7,
        StandardDevice.SystemSubType.WINDOWS_SERVER_2012,
        StandardDevice.SystemSubType.WINDOWS_SERVER_2008,
    ):
        script = r'echo %s>>%s\file.txt' % (file_path, api_settings.WINDOWS_BASE_DIR)
    elif system_sub_type in (
        StandardDevice.SystemSubType.WINDOWS_XP,
        StandardDevice.SystemSubType.WINDOWS_SERVER_2003,
    ):
        script = script + r'start /b {file_path}'.format(file_path=file_path)
    elif system_sub_type == StandardDevice.SystemSubType.CENTOS_7:
        if file_path.endswith('.rpm'):
            script = 'rpm -ivh {file}'.format(file=file_path)
    elif system_sub_type in (StandardDevice.SystemSubType.UBUNTU_14, StandardDevice.SystemSubType.UBUNTU_16, StandardDevice.SystemSubType.KALI_2):
        if file_path.endswith('.deb'):
            script = 'apt-get install {file}'.format(file=file_path)
    return script


def generate_default_custom_install_script(file_path, system_sub_type, install_script):
    system_type = StandardDevice.SystemSubTypeMap[system_sub_type]
    # 0不执行 1直接执行 2解压执行
    mode = 0
    file_path_lower = file_path.lower()
    if system_type == StandardDevice.SystemType.WINDOWS:
        template = window_template
        base_dir = api_settings.WINDOWS_BASE_DIR
        if install_script.find('{this}') >= 0:
            file_name = file_path.split('\\')[-1]
            install_script = install_script.replace('{this}', file_name)
            mode = 1
        else:
            if file_path_lower.endswith('.zip') or file_path_lower.endswith('.rar'):
                mode = 2
    else:
        template = linux_template
        base_dir = api_settings.LINUX_BASE_DIR
        if install_script.find('{this}') >= 0:
            file_name = file_path.split('/')[-1]
            install_script = install_script.replace('{this}', file_name)
            mode = 1
        else:
            if file_path.lower().endswith('.zip'):
                mode = 2

    if mode == 1:
        script = template.CUSTOM_NORMAL_INSTALL.format(
            base_dir=base_dir,
            install_script=install_script,
        )
    elif mode == 2:
        script = template.CUSTOM_INSTALL.format(
            file_path=file_path,
            base_dir=base_dir,
            installer_folder=str(uuid.uuid4()),
            install_script=install_script,
        )
    else:
        script = ''
    return script


def fix_win_zh_script(script, spliter):
    return spliter + 'chcp 65001' + spliter + script + spliter + 'chcp 936' + spliter



def _get_installer_resource(system_sub_type, installer, version=None, raise_exception=True):
    for resource in installer['resources']:
        if system_sub_type in resource['platforms']:
            if version:
                if version == resource['version']:
                    return resource
            else:
                return resource
    if raise_exception:
        raise MsgException(error.INSTALLER_RESOURCE_NOT_FOUND)


def _get_installer_resources(system_sub_type, installers_info, raise_exception=True):
    name_map = {installer['name']: installer for installer in api_settings.INSTALLERS}
    resources = []
    for installer_info in installers_info:
        if isinstance(installer_info, (six.string_types, six.text_type)):
            installer_name = installer_info
            installer_version = None
        elif isinstance(installer_info, dict):
            installer_name = installer_info.get('name')
            installer_version = installer_info.get('version')
        elif isinstance(installer_info, (tuple, list)) and len(installer_info) >= 1:
            installer_name = installer_info[0]
            installer_version = installer_info[1] if len(installer_info) >= 2 else None
        else:
            continue

        installer = name_map.get(installer_name)
        if not installer:
            if raise_exception:
                raise MsgException(error.INSTALLER_RESOURCE_NOT_FOUND)
            else:
                continue

        resource = _get_installer_resource(
            system_sub_type,
            installer,
            version=installer_version,
            raise_exception=raise_exception,
        )
        if resource:
            resources.append(resource)
    return resources


def generate_installers_install_script(system_sub_type, installers_info):
    if system_sub_type == StandardDevice.SystemSubType.OTHER:
        return ''

    system_sub_type = system_sub_type
    system_type = StandardDevice.SystemSubTypeMap[system_sub_type]
    spliter = get_spliter(system_sub_type)
    # 生成安装目录
    script = spliter + generate_base_dir_script(system_sub_type) + spliter

    sub_script = spliter
    resources = _get_installer_resources(system_sub_type, installers_info)
    has_default_installer = False
    for resource in resources:
        if resource['file'] and not resource['install_script']:
            has_default_installer = True

    if has_default_installer and system_sub_type in (
            StandardDevice.SystemSubType.WINDOWS_10,
            StandardDevice.SystemSubType.WINDOWS_7,
            StandardDevice.SystemSubType.WINDOWS_SERVER_2012,
            StandardDevice.SystemSubType.WINDOWS_SERVER_2008,
    ):
        installer_tool_urls = [
            settings.SERVER_HOST + static('common_env/tools/windows_installer/1.dll'),
            settings.SERVER_HOST + static('common_env/tools/windows_installer/start.exe'),
        ]
        for installer_tool_url in installer_tool_urls:
            file_path, download_script = generate_file_download_script(installer_tool_url, system_sub_type)
            sub_script = sub_script + download_script + spliter

    for resource in resources:
        if resource['file']:
            file_name = os.path.basename(resource['file'])
            file_url = settings.SERVER_HOST + settings.MEDIA_URL + resource['file']

            is_win_file_contains_zh = system_type == StandardDevice.SystemType.WINDOWS and contain_zh(file_name)
            if is_win_file_contains_zh:
                download_file_name = (str(uuid.uuid4()) + os.path.splitext(file_name)[-1])
            else:
                download_file_name = file_name
            file_path, download_script = generate_file_download_script(file_url, system_sub_type,
                                                                       download_file_name)
            sub_script = sub_script + download_script + spliter

            resource_script = ''
            if is_win_file_contains_zh:
                resource_script = resource_script + 'ren {} {}'.format(file_path, file_name) + spliter
                file_path = file_path.replace(download_file_name, file_name)

            if resource['install_script']:
                resource_install_script = generate_default_custom_install_script(file_path, system_sub_type,
                                                                                 resource['install_script'])
                is_win_script_contains_zh = system_type == StandardDevice.SystemType.WINDOWS and contain_zh(
                    resource_install_script)
                if not is_win_file_contains_zh and is_win_script_contains_zh:
                    resource_install_script = fix_win_zh_script(resource_install_script, spliter)
                resource_script = resource_script + resource_install_script + spliter
            else:
                resource_script = resource_script + generate_default_install_script(file_path,
                                                                                    system_sub_type) + spliter

            if is_win_file_contains_zh:
                resource_script = fix_win_zh_script(resource_script, spliter)

            sub_script = sub_script + resource_script + spliter
        else:
            if resource['install_script']:
                resource_install_script = resource['install_script']
                is_win_script_contains_zh = system_type == StandardDevice.SystemType.WINDOWS and contain_zh(
                    resource_install_script)
                if is_win_script_contains_zh:
                    resource_install_script = fix_win_zh_script(resource_install_script, spliter)
                sub_script = sub_script + resource_install_script + spliter

    if has_default_installer and system_sub_type in (
            StandardDevice.SystemSubType.WINDOWS_10,
            StandardDevice.SystemSubType.WINDOWS_7,
            StandardDevice.SystemSubType.WINDOWS_SERVER_2012,
            StandardDevice.SystemSubType.WINDOWS_SERVER_2008,
    ):
        sub_script = sub_script + r'start /b {base_dir}\start.exe'.format(
            base_dir=api_settings.WINDOWS_BASE_DIR) + spliter

    # windows作成脚本文件安装
    if system_type == StandardDevice.SystemType.WINDOWS:
        made_script_filename = '%s.bat' % uuid.uuid4()
        made_script_path = os.path.join(settings.MEDIA_ROOT, 'tmp_script', made_script_filename)
        with open(made_script_path, 'w') as made_script_file:
            made_script_file.write(sub_script)

        script = script + window_template.MADE_SCRIPT_INSTALL.format(
            base_dir=api_settings.WINDOWS_BASE_DIR,
            file_url=settings.SERVER_HOST + settings.MEDIA_URL + 'tmp_script/' + made_script_filename,
        ) + spliter
    else:
        script = script + sub_script + spliter

    return script



