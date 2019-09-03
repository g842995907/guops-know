# -*- coding: utf-8 -*-
import json
import subprocess

from common_framework.utils.delay_task import new_task
from common_scene.complex.views import BaseScene

from ..base.base import Resource


class Image(Resource):

    def __init__(self, operator=None):
        self.operator = operator or BaseScene()

    def get(self, image_id=None, image_name=None):
        return self.operator.get_image(id=image_id, name=image_name)

    def create(self, image_name, vm_id=None, container_id=None, image_file=None, ftp_file_name=None, meta_data=None, created=None, failed=None, timeout_callback=None):
        check_type = 'Image'
        if vm_id:
            image_id = self.operator.create_snapshot(vm_id, image_name)
            image = self.get(image_id)
            # # snapshot
            # bdm = getattr(image, 'block_device_mapping', None)
            # if bdm:
            #     try:
            #         block_snap_id = json.loads(bdm)[0].get("snapshot_id")
            #         self.operator.check_volume_snapshot_status(block_snap_id)
            #     except Exception:
            #         pass
            # else:
            #     image = self.operator.check_image_status(image_id)
            check_type = 'Snapshot'
        elif container_id:
            image = self.operator.save_image(container_id, image_name)
        elif image_file:
            params = {
                'name': image_name,
                'image_file': image_file,
            }
            if meta_data:
                params.update(meta_data)
            image = self.operator.create_image(**params)
        elif ftp_file_name:
            params = {
                'name': image_name,
                'file_name': ftp_file_name,
            }
            if meta_data:
                params.update(meta_data)
            image =  self.operator.create_image_by_ftp(**params)
        else:
            raise Exception('param error: no resource for creating image')

        if created or failed:
            new_task(self.operator.check_image_status, 0, (image.id, check_type, created, failed, timeout_callback))

        return image

    def update(self, image_id=None, image_name=None, **kwargs):
        partial_update = kwargs.pop('partial_update', True)
        if partial_update:
            remove_props = None
        else:
            all_props = ('hw_disk_bus', 'hw_vif_model', 'hw_video_model')
            remove_props = list(set(all_props) - set(kwargs.keys()))
        self.operator.update_image(image_id or image_name, remove_props=remove_props, **kwargs)

    def delete(self, image_id=None, image_name=None):
        if image_id:
            self.operator.delete_image(image_id)
            self.operator.update_image_cache()
        elif image_name:
            images = self.operator.glance_cli.images_list_by_name(image_name)
            for image in images:
                self.operator.delete_image(image.id)
            if images:
                self.operator.update_image_cache()

    def local_delete_container(self, image_name):
        subprocess.call('docker image rm {name}'.format(name=image_name), shell=True)


    def local_load_container(self, image):
        self.operator.load_docker_image(image)
