# -*- coding: utf-8 -*-
from django.utils import timezone

from common_env.models import Env
from practice import constant
from practice.api import Practice, PRACTICE_TYPE_MAN_MACHINE
from practice.utils.task import get_submit_score, generate_task_hash
from practice_man_machine.models import ManMachineTask, ManMachineCategory
from practice_man_machine.web import serializers as webSerializers
from practice_man_machine.cms import serializers as cmsSerializers


class ManMachinePractice(Practice):
    serializer_class = webSerializers.ManMachineTaskSerializer
    queryset = ManMachineTask.objects.filter(is_copy=False, event__public=True).order_by('-id')
    cms_serializer = cmsSerializers.ManMachineTaskSerializer
    web_serializer = webSerializers.ManMachineTaskSerializer
    task_class = ManMachineTask
    task_category = ManMachineCategory
    category_web_serializer = webSerializers.ManMachineCategorySerializer
    category_cms_serializer = cmsSerializers.ManMachineCategorySerializer

