# -*- coding: utf-8 -*-

# 虚拟机上报地址，下载环境zip包地址, 配置oj floating ip地址和端口
SERVER_IP = "10.98.98.250"
SERVER_PORT = 80
SERVER_HOST = 'http://%s:%s' % (SERVER_IP, SERVER_PORT)
SERVER_INTERNET_IP = '192.168.100.131'
SERVER_INTERNET_HOST = 'http://%s:80' % SERVER_INTERNET_IP
VIS_HOST = '127.0.0.1:8050'
CHECK_VIS_HOST = '127.0.0.1:8050'

XCTF_CONFIG = {
    'common_proxy': {
        'PROXY_IP': '192.168.100.131',
        'SWITCH': True,
    },
    'common_remote': {
        'DATABASE': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'guacamole_db',
            'USER': 'guacamole_user',
            'PASSWORD': 'guacamole_pass',
            'HOST': '172.29.100.225',
            'PORT': '3306'
        },
        'OJ_SERVER': {
            'host_ip': '172.29.100.225',
            'ssh_username': 'root',
            'ssh_password': '123',
        },
        'GUACAMOLE_SERVERS': [{
            'host_ip': '172.29.100.225',
            'server': 'http://172.29.100.225:8080',
            'public_server': 'http://172.29.100.225:8080',
            'ssh_username': 'root',
            'ssh_password': 'ycxx123#',
            # }, {
            #     'host_ip': '192.168.101.132',
            #     'server': 'http://192.168.101.132:8080',
            #     'public_server': 'http://192.168.101.132:8080',
            #     'ssh_username': 'root',
            #     'ssh_password': '123',
        }],
    },
    'common_env': {
        'SERVER_CREATE_POOL_LIMIT': 1000,
        'DOCKER_HOSTS': ['192.168.100.156'],
    },
    'system_configuration': {
        'SSH_HOST_IP': '10.10.50.249',
        'SSH_USERNAME': 'cyberpeace',
    },
    'scene': {
        "OS_AUTH": {
            'auth_url': 'http://controller:35357/v3/',
            'username': 'admin',
            'password': 'ADMIN_PASS',
            # 'password': 'L5uCdcjQQuyY9DLs',
            'project_name': 'admin',
            'project_id': '',
            'user_domain_id': 'default',
            'project_domain_id': 'default'
        },

        # for complex scene
        "COMPLEX_MISC": {
            'external_net': "c957631c-ee68-41d4-b238-59395a703465",
            'linux_flavor': "m2.1c-1g-10g",
            'windows_flavor': "m4.4c-4g-40g",
            'security_groups': [],
            'keypairs': "",
            'ftp_path': "/home/ftp",
            'ftp_proxy_port': 21,
            'controller_root_pwd': "password",
            'clean_env': False,
            'subnet_seg': ['172.19'],
            'ad_subnet_seg': {
                'cidr': '172.{}.{}.{}/24',
                'range': [16, 100]
            },
            'cpu_allocation_ratio': 16,
            'ram_allocation_ratio': 1.5,
            'disk_allocation_ratio': 1.0,
            'dns_nameservers': ['114.114.114.114'],
            'memcache_host': ['127.0.0.1:11211'],
            'report_vm_status': '%s/common_env/update_vm_status/' % SERVER_HOST,
            'report_template_vm_status': '%s/common_env/api/standard_devices/{}/tmp_vm_running/' % SERVER_HOST,
        },
    },
    'x_vulns': {
        'SERVER': 'http://10.10.49.253:8082',
    },
    'dashboard': {
        'ALARM_PERCENT': {
            'cpu_alarm_percent': 80,
            'ram_alarm_percent': 80,
            'disk_alarm_percent': 80
        }
    },
    'COURSE': {
        'NODE_PATH': '/usr/local/bin/node',
    },
    'COMMON_CLOUD': {
        'CLOUD_CENTER': '127.0.0.1:80',
    }
}

DATABASES = {
    'default': {
        # 'ENGINE': 'django.db.backends.mysql',
        'ENGINE': 'common_framework.utils.mysql',
        'NAME': 'cyberpeace',
        'USER': 'cyberpeace',
        'PASSWORD': 'cyberpeace',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.163.com'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'nanjingsainin@163.com'
EMAIL_HOST_PASSWORD = '0608Sainin'
DEFAULT_FROM_EMAIL = 'nanjingsainin@163.com'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

ORGANIZATION_EN = {
    "First_level": "School",
    "Second_level": "Faculty",
    "Third_level": "Major",
    "Fourth_level": "Classes",
}

ORGANIZATION_CN = {
    "First_level": "学校",
    "Second_level": "院系",
    "Third_level": "年级",
    "Fourth_level": "班级",
}

REDIS_PASS = "v105uCdcjQQuCdgww"
