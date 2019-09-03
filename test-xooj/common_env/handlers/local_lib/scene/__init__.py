# -*- coding: utf-8 -*-

from django.core.cache import cache

from common_scene.clients.glance_client import Client as GlanceClient
from common_scene.setting import api_settings as scene_api_settings
from common_env.setting import api_settings

from .scene.docker import Docker
from .scene.vm import Vm
from .scene.qos import Qos
from .scene.image import Image
from .scene.network import Network
from .scene.router import Router
from .scene.firewall import Firewall
from .scene.volume import Volume


docker = Docker()
vm = Vm()
qos = Qos()
image = Image()
network = Network()
router = Router()
firewall = Firewall()
volume = Volume()

external_net = scene_api_settings.COMPLEX_MISC['external_net']


def get_base_images():
    base_images = cache.get('openstack_base_images') or []
    if base_images:
        return base_images

    images = GlanceClient().image_get_all()
    for image in images:
        if image.name in api_settings.BASE_IMAGES:
            base_images.append({
                'id': image.id,
                'name': image.name,
                'detail': api_settings.BASE_IMAGE[image.name]
            })
    base_images.sort(key=lambda x: api_settings.BASE_IMAGES.index(x['name']))
    cache.set('openstack_base_images', base_images, None)
    return base_images
