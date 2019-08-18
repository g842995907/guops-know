import os
import shutil

from django.db.models import Q

from base.utils.resource.api import ResourceHandler
from base_cloud import api as cloud
from base_scene.utils.resource import get_scene_config_related_images
from base_scene.models import StandardDevice, StandardDeviceSnapshot
from base_monitor.models import Scripts
from base_mission.models import Mission
from traffic_event.models import TrafficEvent

from cr_scene import app_settings


def cr_scene_extra_export_handle(cr_scenes, tmp_dir):
    images = set()
    for cr_scene in cr_scenes:
        images.update(get_scene_config_related_images(cr_scene.scene_config))

        script_ids = set()
        for mission in cr_scene.missions.exclude(status=Mission.Status.DELETE):
            if hasattr(mission, 'checkmission'):
                script_ids.add(mission.checkmission.script_id)
        scripts = Scripts.objects.filter(id__in=script_ids)
        images.update([script.checker.name for script in scripts if script.checker])

        for traffic_event in cr_scene.traffic_events.exclude(status=TrafficEvent.Status.DELETE):
            if hasattr(traffic_event.traffic, 'background_traffic'):
                device = traffic_event.traffic.background_traffic.trm
                if device:
                    images.add(device.name)

            if hasattr(traffic_event.traffic, 'intelligent_traffic'):
                device = traffic_event.traffic.intelligent_traffic.tgm
                if device:
                    images.add(device.name)

    devices = StandardDevice.objects.filter(
        Q(standarddevicesnapshot__name__in=images) | Q(name__in=images)
    )

    snapshots = StandardDeviceSnapshot.objects.filter(
        Q(standard_device__name__in=images) | Q(name__in=images)
    )

    image_names = []
    device_map = {device.name: device for device in devices}
    snapshot_names = list(set([snapshot.name for snapshot in snapshots]))
    all_images = [image.name for image in cloud.image.operator.glance_cli.image_get_all()]

    for device_name, device in device_map.items():
        if device_name in all_images:
            image_names.append(device_name)

        if device.image_type == StandardDevice.ImageType.VM and device_name not in snapshot_names:
            try:
                snapshot = cloud.volume.get(snapshot_name=device_name)
            except Exception:
                snapshot = None
            else:
                if snapshot:
                    snapshot_names.append(device_name)

    images_str = '\n'.join(image_names)
    images_file_path = os.path.join(tmp_dir, 'images')
    with open(images_file_path, 'w') as images_file:
        images_file.write(images_str)

    snapshots_str = '\n'.join(snapshot_names)
    snapshot_file_path = os.path.join(tmp_dir, 'snapshots')
    with open(snapshot_file_path, 'w') as snapshots_file:
        snapshots_file.write(snapshots_str)


resource_zip_filename = 'data.zip'


def get_tmp_dir_name(zip_file_name):
    if zip_file_name.endswith('.zip'):
        return zip_file_name[:-4]
    else:
        return zip_file_name + '.tmp'


def prepare_tmp_dir(zip_file_path):
    base_dir = os.path.dirname(zip_file_path)
    filename = os.path.basename(zip_file_path)

    tmp_dir = os.path.join(base_dir, get_tmp_dir_name(filename))
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)

    return tmp_dir


def export_cr_scenes(cr_scenes):
    resource_handler = ResourceHandler()
    zip_file_path = resource_handler.export_package(cr_scenes, password=app_settings.CR_SCENE_PACK_PASSWORD)
    tmp_dir = prepare_tmp_dir(zip_file_path)

    resource_zip_path = os.path.join(tmp_dir, resource_zip_filename)
    try:
        shutil.move(zip_file_path, resource_zip_path)
        cr_scene_extra_export_handle(cr_scenes, tmp_dir)
        zip_file_path = ResourceHandler.pack_zip(tmp_dir)
    finally:
        shutil.rmtree(tmp_dir)

    return zip_file_path


def import_cr_scenes(zip_file_path):
    tmp_dir = prepare_tmp_dir(zip_file_path)

    try:
        ResourceHandler.unpack_zip(zip_file_path, tmp_dir)

        resource_zip_path = os.path.join(tmp_dir, resource_zip_filename)

        resource_handler = ResourceHandler()
        resource_handler.import_package(resource_zip_path, password=app_settings.CR_SCENE_PACK_PASSWORD)
    finally:
        shutil.rmtree(tmp_dir)
