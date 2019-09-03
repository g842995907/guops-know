# -*- coding: utf-8 -*-
from django.utils import timezone
from common_env.models import Env

from practice import constant
from practice.api import Practice, PRACTICE_TYPE_EXCRISE
from practice.utils.task import get_submit_score, generate_task_hash
from practice_exercise.models import PracticeExerciseTask, PracticeExerciseCategory
from practice_exercise.web import serializers as webSerializers
from practice_exercise.cms import serializers as cmsSerializers


class ExercisePractice(Practice):
    serializer_class = webSerializers.PracticeExerciseTaskSerializer
    queryset = PracticeExerciseTask.objects.filter(is_copy=False, event__public=True).order_by('lock', '-id', )
    cms_serializer = cmsSerializers.PracticeExerciseTaskSerializer
    web_serializer = webSerializers.PracticeExerciseTaskSerializer
    task_class = PracticeExerciseTask
    task_category = PracticeExerciseCategory
    category_web_serializer = webSerializers.PracticeExerciseCategorySerializer
    category_cms_serializer = cmsSerializers.PracticeExerciseCategorySerializer



