# -*- coding: utf-8 -*-
import logging
import os
import subprocess
import uuid

from django.conf import settings
from rest_framework import viewsets, filters, response, exceptions
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache

from cloud_client import models as cloud_models
from cloud_client.cms import serializers
from common_framework.utils import x_rsa
from common_framework.utils.constant import Status
from common_framework.utils.delay_task import new_task
from common_framework.utils.django_cmd import django_manage
from common_framework.utils.rest import mixins as common_mixins
from common_framework.utils.zip import ZFile
from common_product import products
from common_product import products_all

from cloud_client.setting import api_settings
from cloud_client.cms import error
from system_configuration.models import SystemConfiguration
import time
from cloud_client.utils.file_operation import UpdateOperation

logger = logging.getLogger()

class UpdateViewSet(common_mixins.CacheModelMixin,
                    common_mixins.DestroyModelMixin,
                    common_mixins.RequestDataMixin,
                    viewsets.ModelViewSet):
    queryset = cloud_models.UpdateInfo.objects.filter(status=Status.NORMAL)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.UpdateSerializer
    related_cache_class = ()

    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('id',)
    ordering = ('-id',)
    search_fields = ('name',)

    def list(self, request, *args, **kwargs):
        return response.Response([])

    def sub_perform_create(self, serializer):
        serializer.save()
        instance = serializer.instance
        file_path = instance.encrypt_file.path

        try:
            extract_to_path = self.unzip(file_path, serializer)
            new_task(self._do_update, 0, (extract_to_path,))
        except Exception as e:
            logger.error("update error msg[%s]", str(e))
            raise exceptions.ValidationError(error.WRONG_UPDATE_ZIP)

        return True

    def _do_update(self, extract_to_path):
        # 升级
        self._update(extract_to_path)

        # 修改版本号
        self.update_version(extract_to_path)

        # # 删除压缩包
        # import shutil
        # shutil.rmtree(extract_to_path)

        self.clear_cache()
        # 重启oj
        self._restart_oj(extract_to_path)

    def unzip(self, file_path, serializer):
        private_key = os.path.join(settings.BASE_DIR, "media", "key", "lic", "key.pem")
        if not os.path.exists(private_key):
            self.clear_cache()
            serializer.save(update_status=cloud_models.UpdateInfo.Status.UPDATE_FAIL)
            raise exceptions.ValidationError()

        zip_path = "/tmp/%s.zip" % str(uuid.uuid4())
        try:
            x_rsa.x_decrypt(file_path, zip_path, private_key)
        except Exception, e:
            serializer.save(update_status=cloud_models.UpdateInfo.Status.UPDATE_FAIL)
            self.clear_cache()
            raise exceptions.ValidationError()

        unzip_path = "/tmp/%s" % str(uuid.uuid4())
        zfile = ZFile(zip_path)

        password = api_settings.update_zip
        if password and len(password) > 0:
            zfile.setpw(password)

        zfile.extract_to(unzip_path)

        return unzip_path

    def sub_perform_destroy(self, instance):
        instance.status = Status.DELETE
        instance.save()
        return True

    def _run_cmd(self, args):
        process = subprocess.Popen(args, env=os.environ.copy(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   shell=True)
        output, error = process.communicate()

        return process.returncode, output, error

    # -- path
    #          --package
    #          --sh
    def _update(self, path):
        sh_path = os.path.join(path, 'sh')
        # package_path = os.path.join(path, 'package')
        package_path = path

        cache.set('update-state', 'updateStart')

        # backup
        try:
            logger.info("update step 1, backup begin...")
            django_manage('backup_files')
        except Exception as e:
            logger.info("Backup Failed: {}".format(e))
            raise Exception(e)
        logger.info("update step 1, backup end...")

        cache.set('update-state', 'backupEnd')

        # before update
        before_sh = os.path.join(sh_path, 'before_update.sh')
        if os.path.exists(before_sh):
            os.chmod(before_sh, 0777)
            args = [before_sh, path]
            c, o, e = self._run_cmd(args)

        # pip package, make migrations, 临时注释
        if os.path.exists(package_path):
            self._pip_install(package_path)

        cache.set('update-state', 'installEnd')

        # remove backup
        try:
            logger.info("update step 3, backup remove begin...")
            django_manage('remove_backup')
        except Exception as e:
            logger.info("Backup Remove Failed: {}".format(e))
            raise Exception(e)
        logger.info("update step 3, backup remove end...")

        cache.set('update-state', 'backupRemoveEnd')

        # after update
        after_sh = os.path.join(sh_path, 'after_update.sh')
        if os.path.exists(after_sh):
            os.chmod(after_sh, 0777)
            args = [after_sh, path]
            c, o, e = self._run_cmd(args)

        time.sleep(1)
        cache.set('update-state', 'updateEnd')

    def _pip_install(self, package_path):
        operation = UpdateOperation()

        if not os.path.exists(package_path):
            return

        logger.info("update step 2, update files begin....")
        # for dirpath, dirnames, filenames in os.walk(package_path):
        #     for filename in filenames:
        #         app_name = filename.split("-")[0]
        #         logger.info("pip install app[%s] filename[%s]", app_name, filename)
        #         if app_name in products_all.ALL_PRODUCT or app_name in products.BASE_APP:
        #             args = ['pip install %s  -t /home/x-oj --upgrade' % os.path.join(dirpath, filename)]
        #             self._run_cmd(args)
        file_path = os.path.join(package_path, 'update')
        if os.path.exists(file_path) and os.path.isdir(file_path):
            operation.update_files(file_path, settings.BASE_DIR)
        else:
            operation.update_files(package_path, settings.BASE_DIR)

        logger.info("update step 2, update files end....")

        operations = operation.django_operations
        if 'migrate' in operations:
            logger.info("update step 2, migrate begin....")
            django_manage('migrate')
            logger.info("update step 2, migrate end....")

        if 'collectstatic' in operations:
            logger.info("update step 2, collectstatic begin....")
            django_manage('collectstatic', '--noinput')
            logger.info("update step 2, mcollectstatic end....")

        if 'compilemessages' in operations:
            logger.info("update step 2, compilemessages begin....")
            django_manage('compilemessages')
            logger.info("update step 2, compilemessages end....")

        return True

    def update_version(self, path):
        version_path = os.path.join(path, 'version')
        if not os.path.exists(version_path):
            return

        with open(version_path, 'r') as f1:
            version = f1.readline()

        sc_verson = SystemConfiguration.objects.filter(key='version').first()
        if sc_verson:
            sc_verson.value = version
            sc_verson.save()
        else:
            SystemConfiguration.objects.create(key='version', value=version)

            # package = "system_configuration"
            # init_py = open(os.path.join(package, '__init__.py')).read()
            # version = re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)
            # SystemConfiguration.objects.create(key='version', value=version)

    def _restart_oj(self, sh_path):
        # restart oj
        logger.info("update step 4, restart oj begin....")
        restart_sh = os.path.join(sh_path, 'restart_oj.sh')
        if os.path.exists(restart_sh):
            os.chmod(restart_sh, 0777)
            args = [restart_sh]
            c, o, e = self._run_cmd(args)
        logger.info("update step 4, restart oj end.....")

    @list_route(methods=['post'], )
    def update_online(self, request):
        zip_url = self.shift_data.get('url')
        file_path = "/tmp/%s.zip" % str(uuid.uuid4())

        import requests
        r = requests.get(zip_url, stream=True)
        with open(file_path, "wb") as zip:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    zip.write(chunk)

        extract_to_path = self.unzip(file_path)

        new_task(self._do_update, 0, (extract_to_path,))
        return response.Response({'status': 'ok'})


        # class UpdateViewSet(common_mixins.CacheModelMixin,
        #                     common_mixins.DestroyModelMixin,
        #                     viewsets.ModelViewSet):
        #     queryset = cloud_models.UpdateInfo.objects.filter(status=Status.NORMAL)
        #     permission_classes = (IsAuthenticated,)
        #     serializer_class = serializers.UpdateSerializer
        #     related_cache_class = ()
        #
        #     filter_backends = (filters.SearchFilter, filters.OrderingFilter)
        #     ordering_fields = ('id',)
        #     ordering = ('-id',)
        #     search_fields = ('name',)
        #
        #     def sub_perform_create(self, serializer):
        #         serializer.save()
        #         instance = serializer.instance
        #         file_path = instance.encrypt_file.path
        #
        #         private_key = os.path.join(settings.BASE_DIR, "media", "key", "private_key")
        #         if not os.path.exists(private_key):
        #             self.clear_cache()
        #             serializer.save(update_status=cloud_models.UpdateInfo.Status.UPDATE_FAIL)
        #             raise exceptions.ValidationError({'msg': gettext('私钥不存在')})
        #
        #         zip_path = "/tmp/%s.zip" % str(uuid.uuid4())
        #         try:
        #             x_rsa.x_decrypt(file_path, zip_path, private_key)
        #         except Exception, e:
        #             serializer.save(update_status=cloud_models.UpdateInfo.Status.UPDATE_FAIL)
        #             self.clear_cache()
        #             raise exceptions.ValidationError({'msg': gettext('密钥不正确，或者升级包不正确')})
        #
        #         extract_to_path = "/tmp/%s" % str(uuid.uuid4())
        #         try:
        #             ZFile(zip_path).extract_to(extract_to_path)
        #         except ValueError, e:
        #             self.clear_cache()
        #             serializer.save(update_status=cloud_models.UpdateInfo.Status.UPDATE_FAIL)
        #             raise exceptions.ValidationError({'msg': gettext('升级包不正确')})
        #
        #         # 升级
        #         os.remove(zip_path)
        #         self._update(extract_to_path)
        #
        #         # 删除压缩包
        #         import shutil
        #         shutil.rmtree(extract_to_path)
        #         serializer.save(update_status=cloud_models.UpdateInfo.Status.UPDATE_OK)
        #
        #         # 重启oj
        #         self._restart_oj(extract_to_path)
        #
        #         return True
        #
        #     def sub_perform_destroy(self, instance):
        #         instance.status = Status.DELETE
        #         instance.save()
        #         return True
        #
        #     def _run_cmd(self, args):
        #         process = subprocess.Popen(args, env=os.environ.copy(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        #                                    shell=True)
        #         output, error = process.communicate()
        #
        #         return process.returncode, output, error
        #
        #     # -- path
        #     #          --package
        #     #          --sh
        #     def _update(self, path):
        #         sh_path = os.path.join(path, 'sh')
        #         package_path = os.path.join(path, 'package')
        #
        #         # before update
        #         before_sh = os.path.join(sh_path, 'before_update.sh')
        #         if os.path.exists(before_sh):
        #             os.chmod(before_sh, 0777)
        #             args = [before_sh, path]
        #             c, o, e = self._run_cmd(args)
        #
        #         # pip package, make migrations
        #         if os.path.exists(package_path):
        #             self._pip_install(package_path)
        #
        #         # after update
        #         after_sh = os.path.join(sh_path, 'after_update.sh')
        #         if os.path.exists(after_sh):
        #             os.chmod(after_sh, 0777)
        #             args = [after_sh, path]
        #             c, o, e = self._run_cmd(args)
        #
        #
        #
        #     def _pip_install(self, package_path):
        #         if not os.path.exists(package_path):
        #             return
        #
        #         logger.info("update step 2, pip install begin....")
        #         for dirpath, dirnames, filenames in os.walk(package_path):
        #             for filename in filenames:
        #                 app_name = filename.split("-")[0]
        #                 logger.info("pip install app[%s] filename[%s]", app_name, filename)
        #                 if app_name in products.ALL_PRODUCT or app_name in products.BASE_APP:
        #                     args = ['pip install %s  -t /home/x-oj/ --upgrade' % os.path.join(dirpath,filename)]
        #                     self._run_cmd(args)
        #
        #         logger.info("update step 2, pip install end....")
        #
        #         # 数据库更新
        #         logger.info("update step 2, migrate begin....")
        #         django_manage('migrate')
        #         logger.info("update step 2, migrate end....")
        #
        #         logger.info("update step 2, collectstatic begin....")
        #         django_manage('collectstatic', '--noinput')
        #         logger.info("update step 2, mcollectstatic end....")
        #
        #         logger.info("update step 3, compilemessages begin....")
        #         django_manage('compilemessages')
        #         logger.info("update step 3, compilemessages end....")
        #
        #         return True
        #
        #     def _restart_oj(self, sh_path):
        #         # restart oj
        #         logger.info("update step 4, restart oj begin....")
        #         restart_sh = os.path.join(sh_path, 'restart_oj.sh')
        #         if os.path.exists(restart_sh):
        #             os.chmod(restart_sh, 0777)
        #             args = [restart_sh]
        #             c, o, e = self._run_cmd(args)
        #         logger.info("update step 4, restart oj end.....")
