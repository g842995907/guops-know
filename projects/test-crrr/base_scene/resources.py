from base.utils.resource.config import Resource

from base_scene.utils.resource import get_scene_config_related_devices

from . import models


class SceneConfig(Resource):
    model = models.SceneConfig
    options = [{
        'to_many': {
            'standard_devices': {
                'get': get_scene_config_related_devices,
                'set': None,
            },
        },
        'force': {
            'user_id': 1,
            'modify_user_id': 1,
        },
        'check': {
            'conflict_consistency_fields': ('json_config', 'file'),
        },
    }]


class StandardDevice(Resource):
    model = models.StandardDevice
    options = [{
        'to_many': {
            'snapshot': {
                'get': lambda obj: models.StandardDeviceSnapshot.objects.filter(standard_device=obj),
                'set': None,
            },
        },
        'force': {
            'image_status_updated_id': None,
            'error': None,
            'image_scene_id': None,
            'user_id': 1,
            'modify_user_id': 1,
        },
        'check': {
            'conflict_consistency_fields': (
                'name', 'description', 'logo', 'install_scripts', 'role', 'role_type', 'is_real',
                'gateway_port_configs', 'image_type', 'system_type',  'system_sub_type',
                'source_image_name', 'disk_format', 'flavor', 'access_mode', 'access_port',
                'access_connection_mode', 'access_user', 'access_password', 'init_support',
                'image_status', 'port_map', 'remote_address'
            ),
        },
    }]


class StandardDeviceSnapshot(Resource):
    model = models.StandardDeviceSnapshot
    options = [{
        'to_one': {
            'standard_device': {},
        },
        'check': {
            'get_conflict': lambda obj: models.StandardDeviceSnapshot.objects.filter(name=obj.name).first(),
            'conflict_consistency_fields': ('name', 'desc'),
        },
    }]
