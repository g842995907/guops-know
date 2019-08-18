import base64
import json
import os
import pyminizip
import shutil
import zlib

from django.utils import timezone

from base import app_settings
from base.utils.text import rk
from base.utils.udir import list_files

from .exception import ResourceException
from .execute import Dumper, Loader


def dump_resource_data(resource_data):
    data = {
        'root': resource_data['root'],
        'index': resource_data['index'],
        'data': resource_data['data'],
    }

    data_str = json.dumps(data, ensure_ascii=False)
    data_str = zlib.compress(data_str)
    data_str = base64.b64encode(data_str)
    return data_str


def load_resource_data(data_str):
    data_str = base64.b64decode(data_str)
    data_str = zlib.decompress(data_str)
    data = json.loads(data_str)
    return data


def random_filename():
    return '{}-{}'.format(timezone.now().strftime('%Y%m%d%H%M%S'), rk())


class ResourceHandler(object):

    data_file_name = 'data'

    def __init__(self, **kwargs):
        self.dump_resource_data = kwargs.get('dump_resource_data', dump_resource_data)
        self.load_resource_data = kwargs.get('load_resource_data', load_resource_data)

        self.extra_export_handle = kwargs.get('extra_export_handle')
        self.extra_import_handle = kwargs.get('extra_import_handle')

    @classmethod
    def prepare_tmp_dir(cls, filename=None):
        filename = filename or random_filename()
        tmp_dir = os.path.join(app_settings.RESOURCE_TMP_DIR, filename)
        os.makedirs(tmp_dir)
        return tmp_dir

    def dumps(self, root_objs, tmp_dir):
        data = Dumper(root_objs).dumps(tmp_dir)
        data_str = self.dump_resource_data(data)
        with open(os.path.join(tmp_dir, self.data_file_name), 'w') as data_file:
            data_file.write(data_str)

        return data_str

    def loads(self, tmp_dir):
        data_file_path = os.path.join(tmp_dir, self.data_file_name)
        if os.path.exists(data_file_path):
            with open(data_file_path, 'r') as data_file:
                data_str = data_file.read()
                data = self.load_resource_data(data_str)
            Loader().loads(data, tmp_dir)
        else:
            raise ResourceException('invalid package: no data file found')

        return data

    @classmethod
    def pack_zip(cls, tmp_dir, password=None):
        zip_file_path = '{}.zip'.format(tmp_dir)
        files = list_files(tmp_dir, True)
        file_prefixs = []
        for file_path in files:
            file_dir = os.path.dirname(file_path)
            file_prefix = file_dir.replace(tmp_dir, '') or '/'
            file_prefixs.append(file_prefix)

        pyminizip.compress_multiple(
            files,
            file_prefixs,
            zip_file_path,
            password,
            5,
        )

        return zip_file_path

    @classmethod
    def unpack_zip(cls, zip_file, tmp_dir, password=None):
        pyminizip.uncompress(zip_file, password, tmp_dir, False)

    def export_package(self, root_objs, filename=None, password=None):
        tmp_dir = self.prepare_tmp_dir(filename=filename)

        try:
            self.dumps(root_objs, tmp_dir)
            if self.extra_export_handle:
                self.extra_export_handle(root_objs, tmp_dir)
            zip_file_path = self.pack_zip(tmp_dir, password=password)
        finally:
            shutil.rmtree(tmp_dir)

        return zip_file_path

    def import_package(self, package_file, password=None):
        tmp_dir = self.prepare_tmp_dir()

        try:
            self.unpack_zip(package_file, tmp_dir, password=password)
            if self.extra_import_handle:
                self.extra_import_handle(tmp_dir)
            self.loads(tmp_dir)
        finally:
            shutil.rmtree(tmp_dir)
