# -*- coding:utf-8 -*-
import os
import re
import subprocess

models_pat = re.compile('.*/models[/.]py$')
static_pat = re.compile('.*[/.][j|cs]s$')
language_pat = re.compile('.*[/.][p|m]o$')

cmd_dict = {
    'migrate': models_pat,
    'collectstatic': static_pat,
    'compilemessages': language_pat
}


class FileOperation(object):
    """
    升级中使用到的文件操作
    所有文件夹必须使用 / 结尾
    """
    PROCESS = subprocess.Popen
    CMD_DICT = cmd_dict

    def __init__(self):
        self.process = self.PROCESS

    def _excute(self, cmd):
        process = self.process(cmd, env=os.environ.copy(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               shell=True)
        output, error = process.communicate()
        print output
        if error:
            raise Exception(error)

    def mk_dir(self, dir_path):
        mkdir_cmd = 'mkdir -p {}'.format(dir_path)
        self._excute(mkdir_cmd)

    def check_dir(self, abs_path):
        dir_path, file_path = os.path.split(abs_path)
        if os.path.exists(dir_path):
            pass
        else:
            self.mk_dir(dir_path)

    def mv_file(self, source_file, destination_file):
        mv_cmd = 'mv {source} {destination}'.format(source=source_file, destination=destination_file)
        self._excute(mv_cmd)

    def list_dir(self, dir):
        files = list()
        for file in os.listdir(dir):
            file_path = os.path.join(dir, file)
            if os.path.isdir(file_path):
                files.extend(self.list_dir(file_path))
            else:
                files.append(file_path)
        return files


class UpdateOperation(FileOperation):
    OPERATION = set()

    @property
    def django_operations(self):
        return self.OPERATION

    def check_operation(self, filename):
        for key, value in self.CMD_DICT.items():
            if value.search(filename):
                self.OPERATION.add(key)

    def update_files(self, source_dir, destination_dir, ignores=None):
        if ignores is None:
            ignores = []
        files = self.list_dir(source_dir)
        for source in files:
            destination = source.replace(source_dir, destination_dir)
            if destination not in ignores:
                self.check_dir(destination)
                self.mv_file(source, destination)

            if len(self.OPERATION) != 3:
                self.check_operation(destination)
                for operate in self.OPERATION:
                    try:
                        self.CMD_DICT.pop(operate)
                    except KeyError:
                        pass
