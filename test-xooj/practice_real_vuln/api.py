# -*- coding: utf-8 -*-
from django.utils import timezone

from common_env.models import Env
from practice import constant
from practice.api import Practice, PRACTICE_TYPE_REAL_VULN
from practice.utils.task import get_submit_score, generate_task_hash
from practice_real_vuln.models import RealVulnTask, RealVulnCategory
from practice_real_vuln.web import serializers as webSerializers
from practice_real_vuln.cms import serializers as cmsSerializers


class RealVulnPractice(Practice):
    serializer_class = webSerializers.RealVulnTaskSerializer
    queryset = RealVulnTask.objects.filter(is_copy=False, event__public=True).order_by('lock', '-id')
    cms_serializer = cmsSerializers.RealVulnTaskSerializer
    web_serializer = webSerializers.RealVulnTaskSerializer
    task_class = RealVulnTask
    task_category = RealVulnCategory
    category_web_serializer = webSerializers.RealVulnCategorySerializer
    category_cms_serializer = cmsSerializers.RealVulnCategorySerializer


