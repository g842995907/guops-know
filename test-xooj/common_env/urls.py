# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from . import api


urlpatterns = [
    url(r'^update_vm_status/$', api.update_vm_status, name='update_vm_status'),
    url(r'^api/standard_devices/(?P<pk>[0-9]+)/tmp_vm_running/$', api.tmp_vm_running, name='tmp_vm_running'),
    url(r'^login_guacamole/$', api.login_guacamole, name='login_guacamole'),

    url(r'^pause_env/$', api.pause_env, name='pause_env'),
    url(r'^recover_env/$', api.recover_env, name='recover_env'),
    url(r'^env_status/$', api.env_status, name='env_status'),
    url(r'^env_flow_data/$', api.env_flow_data, name='env_flow_data'),
    url(r'^envgateway_static_route/$', api.envgateway_static_route, name='envgateway_static_route'),
    url(r'^envgateway_firewall_rule/$', api.envgateway_firewall_rule, name='envgateway_firewall_rule'),
    url(r'^envterminal_status/$', api.envterminal_status, name='envterminal_status'),
    url(r'^envterminal/$', api.envterminal, name='envterminal'),
    url(r'^recreate_envterminal/$', api.recreate_envterminal, name='recreate_envterminal'),
    url(r'^restart_envterminal/$', api.restart_envterminal, name='restart_envterminal'),
    url(r'^envterminal_console_url/$', api.envterminal_console_url, name='envterminal_console_url'),
    url(r'^envterminal_first_boot/$', api.envterminal_first_boot, name='envterminal_first_boot'),
    url(r'^envnet/$', api.envnet, name='envnet'),
    url(r'^envattacker/$', api.envattacker, name='envattacker'),
    url(r'^envattacker_status/$', api.envattacker_status, name='envattacker_status'),
    url(r'^base_images/$', api.base_images, name='base_images'),
    url(r'^flavors/$', api.flavors, name='flavors'),
    url(r'^using_env_objects/$', api.using_env_objects, name='using_env_objects'),
    url(r'^installers/$', api.installers, name='installers'),
]

