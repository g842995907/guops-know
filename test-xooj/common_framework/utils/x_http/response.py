import os
import pyminizip as pyminizip
import uuid

from django.http.response import FileResponse

from common_framework.utils.zip import Ziper


class MultipleFileResponse(FileResponse):
    def __init__(self, file_list, password=None, *args, **kwargs):
        # _zip_o = Ziper()
        #
        # for _file_path in file_list:
        #     if os.path.exists(_file_path):
        #         with open(_file_path) as file_o:
        #             file_content = file_o.read()
        #
        #             file_name_idx = _file_path.rfind('/') + 1
        #             file_name = _file_path[file_name_idx:]
        #
        #             _zip_o.add(file_name, file_content)
        #
        # zf = zipfile.ZipFile(_zip_o.in_memory_zip, mode='r')
        # zf.setpassword('wwww')
        # zf.close()

        tmp_name = "/tmp/{}.zip".format(str(uuid.uuid4()))
        if len(file_list) == 0:
            _zip_o = Ziper()
            content = _zip_o.read()
        else:
            pyminizip.compress_multiple(file_list, tmp_name, password, 4)

            content = None
            with open(tmp_name) as _t:
                content = _t.read()
            os.remove(tmp_name)

        super(MultipleFileResponse, self).__init__(content, *args, **kwargs)
