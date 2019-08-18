# -*- coding: utf-8 -*-
import os
import uuid
import shutil

from django.conf import settings

from .utils import backup, file_upgrade, zip, command, decorator

# CR_PATH = '/home/cr'
CR_PATH = settings.BASE_DIR
WEB_PATH = '/home/web'
CMS_PATH = '/home/cms'


@decorator.upgrade_status_log
def upgrade_system(sender, instance=None, created=False, **kwargs):
    if created:
        # 解压升级包
        tmp_path = os.path.join('/tmp', str(uuid.uuid4()))
        zipper = zip.ZipOperation(instance.upgrade_package, tmp_path)
        zipper.unzip()

        # 项目文件，数据库备份，每次备份会删除上次备份
        backup_operation = backup.BackupOperation()
        backup_operation.raise_backup()

        cr_path = os.path.join(tmp_path, 'cr')
        sh_path = os.path.join(tmp_path, 'sh')
        web_path = os.path.join(tmp_path, 'web')
        cms_path = os.path.join(tmp_path, 'cms')

        cmd = command.Command()
        # 升级前脚本
        before_sh = os.path.join(sh_path, 'before_upgrade.sh')
        if os.path.exists(before_sh):
            cmd.run_shell(before_sh)

        # web 升级
        if os.path.exists(web_path):
            shutil.rmtree(WEB_PATH)
            shutil.move(web_path, WEB_PATH)

        # cms 升级
        if os.path.exists(cms_path):
            shutil.rmtree(CMS_PATH)
            shutil.move(cms_path, CMS_PATH)

        # cr 升级
        if os.path.exists(cr_path):
            upgrade = file_upgrade.UpdateFileOperation(cr_path, CR_PATH)
            upgrade.update_files()

        # 根据升级文件执行django操作
        models_files, language_files = file_upgrade.raise_django_operations(
            file_upgrade.FileOperation.list_dir(tmp_path)
        )
        if models_files:
            cmd.django_migrate()
        if language_files:
            cmd.django_compilemessages()

        # 升级后脚本
        after_sh = os.path.join(sh_path, 'after_upgrade.sh')
        if os.path.exists(after_sh):
            cmd.run_shell(after_sh)

        # 版本号更新
        version_path = os.path.join(tmp_path, 'version')
        if os.path.join(version_path):
            with open(version_path, 'r') as f:
                version = f.readline()
            instance.version = version.split('\n')[0]
            instance.save()

        # 清理临时文件
        zipper.clear_tmp()

        # 重启cr项目
        cmd.run_cmd('supervisorctl restart cr')
