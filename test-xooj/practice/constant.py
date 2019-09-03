# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from common_framework.utils.enum import enum

TaskEventStatus = enum(
    DELETE=0,
    NORMAL=1,
)

TaskStatus = enum(
    DELETE=0,
    NORMAL=1,
)

CategoryStatus = enum(
    DELETE=0,
    NORMAL=1,
)

Difficulty = enum(
    INTRUDCTION=0,
    INCREASE=1,
    EXPERT=2
)

TaskEnvStatus = enum(
    TEMPLATE=-1,
    DELETED=0,
    CREATING=1,
    USING=2,
    ERROR=3
)

TaskEnvType = enum(
    SHARED=0,
    PRIVATE=1
)

ImageType = enum(
    LINUX='linux',
    WINDOWS='windows'
)

Role = enum(
    OPERATOR='operator',
    TARGET='target',
    WINGMAN='wingman'
)

Flavor = enum(
    LARGE='large',
    MIDDLE='middle',
    SMALL='small',
    MINI='mini'
)

AccessMode = enum(
    HTTP='http',
    HTTPS='https',
    NC='nc',
    SSH='ssh',
    RDP='rdp',
    VNC='vnc',
    SPICE='spice'
)

AccessModeDefaultPort = {
    AccessMode.HTTP: 80,
    AccessMode.HTTPS: 443,
    AccessMode.NC: 9999,
    AccessMode.SSH: 22,
    AccessMode.RDP: 3389,
    AccessMode.VNC: 6080,
    AccessMode.SPICE: 6082
}

AccessUserModes = (
    AccessMode.SSH,
    AccessMode.RDP,
    AccessMode.VNC,
    AccessMode.SPICE
)

ImageTypeAdminUser = {
    ImageType.LINUX: 'root',
    ImageType.WINDOWS: 'xctf'
}

TaskEnvServerStatus = enum(
    TEMPLATE=-1,
    DELETED=0,
    CREATING=1,
    CREATED=2,
    STARTING=3,
    STARTED=4,
    DEPLOYING=5,
    RUNNING=6,
    ERROR=8,
)

AccessModeProxyPort = {
    AccessMode.HTTP: 'proxy_http_port',
    AccessMode.HTTPS: 'proxy_https_port',
    AccessMode.NC: 'proxy_nc_port',
    AccessMode.SSH: 'proxy_ssh_port',
    AccessMode.RDP: 'proxy_rdp_port',
}


def to_response(data):
    return {
        'error_code': 0x0000,
        'response_data': data
    }


def to_error(code, message):
    return {
        'error_code': code,
        'error_message': message
    }


ALREADY_SUBMITTED = to_error(0x0060, 'choice is already submitted')
ILLEGAL_REQUEST_PARAMETERS = to_error(0x0010, 'illegal request parameters')

TASKEVENT = enum(
    NMAE_HAVE_EXISTED=_("x_name_have_existed"),
    NAME_REQUIRED=_("x_required_field"),
    FIELD_LENGTH_REQUIRED=_('x_long_length_30')
)
