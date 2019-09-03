# -*- coding: utf-8 -*-

from practice.api import Practice
from practice_attack_defense.cms import serializers as cmsSerializers
from practice_attack_defense.models import PracticeAttackDefenseTask, PracticeAttackDefenseCategory
from practice_attack_defense.web import serializers as webSerializers


class AttackDefensePractice(Practice):
    serializer_class = webSerializers.PracticeAttackDefenseTaskSerializer
    queryset = PracticeAttackDefenseTask.objects.filter(is_copy=False, event__public=True).order_by('lock', '-id', )
    cms_serializer = cmsSerializers.PracticeAttackDefenseTaskSerializer
    web_serializer = webSerializers.PracticeAttackDefenseTaskSerializer
    task_class = PracticeAttackDefenseTask
    task_category = PracticeAttackDefenseCategory
    category_web_serializer = webSerializers.PracticeAttackDefenseCategorySerializer
    category_cms_serializer = cmsSerializers.PracticeAttackDefenseCategorySerializer



