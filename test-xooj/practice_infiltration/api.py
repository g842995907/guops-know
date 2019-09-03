# -*- coding: utf-8 -*-
from django.utils import timezone
from common_env.models import Env

from practice import constant
from practice.api import Practice, PRACTICE_TYPE_INFILTRATION
from practice.utils.task import get_submit_score, generate_task_hash
from practice_infiltration.models import PracticeInfiltrationTask, PracticeInfiltrationCategory
from practice_infiltration.web import serializers as webSerializers
from practice_infiltration.cms import serializers as cmsSerializers


class InfiltrationPractice(Practice):
    serializer_class = webSerializers.PracticeInfiltrationTaskSerializer
    queryset = PracticeInfiltrationTask.objects.filter(is_copy=False, event__public=True).order_by('lock', '-id', )
    cms_serializer = cmsSerializers.PracticeInfiltrationTaskSerializer
    web_serializer = webSerializers.PracticeInfiltrationTaskSerializer
    task_class = PracticeInfiltrationTask
    task_category = PracticeInfiltrationCategory
    category_web_serializer = webSerializers.PracticeInfiltrationCategorySerializer
    category_cms_serializer = cmsSerializers.PracticeInfiltrationCategorySerializer



