# -*- coding: utf-8 -*-
import datetime
import os
import time

from django.core.cache import cache
from django.utils import timezone
from django.shortcuts import redirect, reverse
from django.utils.deprecation import MiddlewareMixin

from common_framework.utils import license
from common_framework.utils.license import License
from common_framework.utils.x_logger import load_log_config
from oj import settings
from oj.settings import DEBUG


class LicenseMiddleware(MiddlewareMixin):
    def process_request(self, request):

        load_log_config()
        request.system_name = license.get_system_config('system_name')
        request.platform_logo = license.get_system_config('logo')
        request.copyright = license.get_system_config('copyright')
        request.trial = license.get_system_config('trial')

        if DEBUG:
            return None

        if request.path == reverse('common_web:license_upload'):
            return None

        license_can_use = cache.get("license_expired")

        if license_can_use is not None and license_can_use:
            return None

        # 判断是否过期
        can_use = True
        deadline = license.get_system_config('deadline_time')
        if deadline:
            t = time.strptime(deadline, "%Y-%m-%d %H:%M:%S")
            y, m, d, h, M, s = t[0:6]
            deadline = datetime.datetime(y, m, d, h, M, s)
            if deadline > timezone.now():
                cache.set("license_expired", can_use, 24 * 60 * 60)
                return None

        personal_license_path = os.path.join(settings.MEDIA_ROOT, 'personal_license')
        license_name = "license.zip"
        personal_license_full_path = os.path.join(personal_license_path, license_name)

        # 根据license文件判断
        errcode, info = License().judge_authorize(personal_license_full_path)
        if errcode != 0:
            can_use = False

            # 返回授权页面
            if request.path != reverse('common_web:authorization'):
                return redirect(reverse('common_web:authorization'))

        cache.set("license_expired", can_use, 24 * 60 * 60)
        return None

