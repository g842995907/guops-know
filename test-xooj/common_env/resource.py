# -*- coding: utf-8 -*-
from django.utils.module_loading import import_string


class StandardDeviceMeta(object):
    check = [{
        'get_conflict_obj': lambda resource: resource.model.objects.filter(name=resource.obj.name).first(),
        'conflict_consistency_check': lambda device, conflict_device: \
            device.role == conflict_device.role
            and device.role_type == conflict_device.role_type
            and device.wan_number == conflict_device.wan_number
            and device.lan_number == conflict_device.lan_number
            and device.image_type == conflict_device.image_type
            and device.system_type == conflict_device.system_type
            and device.source_image_name == conflict_device.source_image_name
            and device.disk_format == conflict_device.disk_format
            and device.meta_data == conflict_device.meta_data
            and device.flavor == conflict_device.flavor
            and device.access_mode == conflict_device.access_mode
            and device.access_port == conflict_device.access_port
            and device.access_connection_mode == conflict_device.access_connection_mode
            and device.access_user == conflict_device.access_user
            and device.access_password == conflict_device.access_password
            and device.init_support == conflict_device.init_support
    }]
    subsidiary = [{
        'force': {
            'tmp_vm_id': None,
            'create_user_id': 1,
            'modify_user_id': None,
        },
    }]


class EnvMeta(object):
    check = [{
        'get_conflict_obj': lambda resource: resource.model.objects.filter(
            status=resource.model.Status.TEMPLATE,
            name=resource.obj.name,
        ).first(),
        'conflict_consistency_check': lambda env, conflict_env: \
            env.type == conflict_env.type
            and env.file == conflict_env.file
            and env.json_config == conflict_env.json_config
    }]
    subsidiary = [{
        'force': {
            'user_id': 1,
            'team_id': None,
        },
    }]


class EnvNetMeta(object):
    check = [{
        'get_conflict_obj': lambda resource: resource.model.objects.filter(
            env=resource.obj.env,
            sub_id=resource.obj.sub_id,
        ).first(),
        'conflict_consistency_check': lambda envnet, conflict_envnet: \
            envnet.name == conflict_envnet.name
            and envnet.dns == conflict_envnet.dns
            and envnet.cidr == conflict_envnet.cidr
            and envnet.dhcp == conflict_envnet.dhcp
    }]
    belong_to = [{
        'root': 'common_env.models.Env',
        'parent': 'common_env.models.Env',
        'get': lambda self_model, env: self_model.objects.filter(env=env),
        'set': lambda self, env: setattr(self, 'env', env)
    }]


class EnvGatewayMeta(object):
    check = [{
        'get_conflict_obj': lambda resource: resource.model.objects.filter(
            env=resource.obj.env,
            sub_id=resource.obj.sub_id,
        ).first(),
        'conflict_consistency_check': lambda envgateway, conflict_envgateway: \
            envgateway.name == conflict_envgateway.name
            and envgateway.static_routing == conflict_envgateway.static_routing
            and envgateway.firewall_rule == conflict_envgateway.firewall_rule
    }]
    belong_to = [{
        'root': 'common_env.models.Env',
        'parent': 'common_env.models.Env',
        'get': lambda self_model, env: self_model.objects.filter(env=env),
        'set': lambda self, env: setattr(self, 'env', env)
    }]
    subsidiary = [{
        'subsidiary': {
            'nets': {
                'many_to_many': True,
                'get': lambda self: self.nets.all(),
                'set': lambda self, envnets: self.nets.set(envnets)
            },
        },
    }]


class EnvTerminalMeta(object):
    check = [{
        'get_conflict_obj': lambda resource: resource.model.objects.filter(
            env=resource.obj.env,
            sub_id=resource.obj.sub_id,
        ).first(),
        'conflict_consistency_check': lambda envterminal, conflict_envterminal: \
            envterminal.name == conflict_envterminal.name
            and envterminal.system_type == conflict_envterminal.system_type
            and envterminal.image_type == conflict_envterminal.image_type
            and envterminal.image == conflict_envterminal.image
            and envterminal.role == conflict_envterminal.role
            and envterminal.flavor == conflict_envterminal.flavor
            and envterminal.install_script == conflict_envterminal.install_script
            and envterminal.init_script == conflict_envterminal.init_script
            and envterminal.clean_script == conflict_envterminal.clean_script
            and envterminal.push_flag_script == conflict_envterminal.push_flag_script
            and envterminal.check_script == conflict_envterminal.check_script
            and envterminal.attack_script == conflict_envterminal.attack_script
            and envterminal.checker == conflict_envterminal.checker
            and envterminal.attacker == conflict_envterminal.attacker
            and envterminal.raw_access_modes == conflict_envterminal.raw_access_modes
            and envterminal.external == conflict_envterminal.external
            and envterminal.net_configs == conflict_envterminal.net_configs
    }]
    belong_to = [{
        'root': 'common_env.models.Env',
        'parent': 'common_env.models.Env',
        'get': lambda self_model, env: self_model.objects.filter(env=env),
        'set': lambda self, env: setattr(self, 'env', env)
    }]
    subsidiary = [{
        'subsidiary': {
            'image': {
                'get': lambda self: import_string('common_env.models.StandardDevice').objects.filter(name=self.image).first(),
            },
            'nets': {
                'many_to_many': True,
                'get': lambda self: self.nets.all(),
                'set': lambda self, envnets: self.nets.set(envnets)
            },
        },
    }]


class EnvAttackerMeta(object):
    check = [{
        'get_conflict_obj': lambda resource: resource.model.objects.filter(
            name=resource.obj.name,
        ).first(),
        'conflict_consistency_check': lambda envattacker, conflict_envattacker: \
            envattacker.type == conflict_envattacker.type
            and envattacker.file == conflict_envattacker.file
            and envattacker.json_config == conflict_envattacker.json_config
    }]
    subsidiary = [{
        'force': {
            'create_user_id': 1,
        },
    }]
