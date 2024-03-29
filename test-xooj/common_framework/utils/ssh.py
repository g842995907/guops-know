#!/usr/bin/env python2
# coding=utf-8

import sys
import os

import logging
from paramiko import SSHClient
import paramiko

logger = logging.getLogger('ssh')


class ssh(object):
    def __init__(self, host, port, username, password=None, key_path=None, timeout=5):
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(host, port, username, password, key_filename=key_path)
        except paramiko.BadHostKeyException, e:
            logger.error("SSH HOST KEY ERROR %s - %s" % (host, e))
            raise e
        except paramiko.AuthenticationException, e:
            logger.error("SSH HOST AUTH FAILED %s - %s" % (host, e))
            raise e
        except paramiko.SSHException, e:
            logger.error("SSH TIMEOUT ERROR  %s - %s" % (host, e))
            raise e
        except Exception, e:
            logger.error("SSH ERROR %s - %s" % (host, e))
            raise e

    def exe(self, command, timeout=15, get_pty=False, environment=None):
        try:
            stdin, stdout, stderr = self.client.exec_command(
                command, timeout=timeout, get_pty=get_pty, environment=environment)
            return stdin, stdout, stderr
        except paramiko.SSHException, e:
            logger.error("COMMAND EXEC ERROR %s" % e)
            raise e

    def upload(self, local_path, remote_path):

        self.sftp = self.client.open_sftp()
        try:
            self.sftp.put(local_path, remote_path)
            logger.debug("UPLOAD FILE SUCCESS upload %s to %s success", local_path, remote_path)
        except paramiko.SSHException, e:
            logger.error("UPLOAD FILE FAILED upload %s to %s failed - %s", local_path, remote_path, e)
            raise e

    @staticmethod
    def normalize_dirpath(dirpath):
        while dirpath.endswith("/"):
            dirpath = dirpath[:-1]
        return dirpath

    def upload_dir(self, localpath, remotepath, preserve_perm=True):
        localpath = localpath.encode('utf-8')
        localpath = self.normalize_dirpath(localpath)
        remotepath = self.normalize_dirpath(remotepath)

        sftp = self.client.open_sftp()

        try:
            sftp.chdir(remotepath)
            # localsuffix = localpath.rsplit("/", 1)[1]
            # remotesuffix = remotepath.rsplit("/", 1)[1]
            # if localsuffix != remotesuffix:
            #     remotepath = os.path.join(remotepath, localsuffix)
        except IOError, e:
            pass

        for root, dirs, fls in os.walk(localpath):
            prefix = os.path.commonprefix([localpath, root])
            suffix = root.split(prefix, 1)[1]
            if suffix.startswith("/"):
                suffix = suffix[1:]

            remroot = os.path.join(remotepath, suffix)

            try:
                sftp.chdir(remroot)
            except IOError, e:
                if preserve_perm:
                    mode = os.stat(root).st_mode & 0777
                else:
                    mode = 0777
                self.mkdir(sftp, remroot, mode=mode, intermediate=True)
                sftp.chdir(remroot)

            for f in fls:
                remfile = os.path.join(remroot, f)
                localfile = os.path.join(root, f)
                sftp.put(localfile, remfile)
                if preserve_perm:
                    sftp.chmod(remfile, os.stat(localfile).st_mode & 0777)

    def mkdir(self, sftp, remotepath, mode=0777, intermediate=False):
        remotepath = self.normalize_dirpath(remotepath)
        if intermediate:
            try:
                sftp.mkdir(remotepath, mode=mode)
            except IOError, e:
                self.mkdir(sftp, remotepath.rsplit("/", 1)[0], mode=mode,
                           intermediate=True)
                return sftp.mkdir(remotepath, mode=mode)
        else:
            sftp.mkdir(remotepath, mode=mode)

    def close(self):
        self.client.close()


if __name__ == '__main__':
    client = ssh("10.10.50.88", 22, "root", key_path="/tmp/id_rsa", timeout=5)

    local_subdir = '/tmp/thj'
    remote_subdir = '/tmp/'
    client.upload_dir(local_subdir, remote_subdir)
