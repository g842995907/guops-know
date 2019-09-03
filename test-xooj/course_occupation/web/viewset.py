# -*- coding: utf-8 -*-

from itertools import groupby

from django.db.models import Count
from django.utils.translation import ugettext_lazy as _
from rest_framework import filters, viewsets, exceptions
from rest_framework.permissions import IsAuthenticated

from common_framework.utils.constant import Status
from common_framework.utils.rest import mixins as common_mixins
from course.models import Lesson
from course_occupation.models import OccupationCourse
from course_occupation.response import OccupationError

from course_occupation.web import serializers
from course_occupation import models as course_occupation_models


class OccupationSystemViewSet(common_mixins.CacheModelMixin,
                              viewsets.ReadOnlyModelViewSet):
    queryset = course_occupation_models.OccupationSystem.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.OccupationSystemSerializer

    def get_queryset(self):
        queryset = self.queryset
        queryset = queryset.filter(public=True)
        return queryset

    def extra_handle_list_data(self, data):
        occupation_ids = [row['id'] for row in data]  # 获取所有的职业id
        occupation_courses = []
        occupation_course_list = OccupationCourse.objects.filter(occupation_system_id__in=occupation_ids,
                                                                 status=1).values('occupation_system_id',
                                                                                  'course_id').order_by(
            'occupation_system_id')
        course_id_list = []  # 获取所有的课程id
        for row in occupation_course_list:
            if row['course_id'] not in course_id_list:
                course_id_list.append(row['course_id'])
        for course in occupation_course_list:
            occupation_courses.append(course)
        occupation_course_list = groupby(occupation_courses, key=lambda x: x['occupation_system_id'])  # 根据职业id对课程进行分组
        occupation_course_list = dict([(key, [a for a in group]) for key, group in occupation_course_list])
        lesson_list = Lesson.objects.filter(status=Status.NORMAL).filter(course__id__in=course_id_list).values(
            'course_id').annotate(
            lesson_count=Count('course_id'))  # 计算每个课程中课时的数量
        lesson_list = {row['course_id']: row for row in lesson_list}
        for row in data:
            if occupation_course_list.get(row['id']) is None:
                row['lesson_count'] = 0
            else:
                course_ids = []
                for occupation_course in occupation_course_list.get(row['id']):
                    course_ids.append(occupation_course['course_id'])
                all_count = 0
                for courseid in course_ids:
                    if lesson_list.get(courseid) is not None:
                        all_count += int(lesson_list.get(courseid)['lesson_count'])
                row['lesson_count'] = all_count
        return data


class OccupationIsChoiceViewSet(common_mixins.CacheModelMixin,
                                viewsets.ModelViewSet):
    queryset = course_occupation_models.OccupationIsChoice.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.OccupationIsChoiceSerializer

    def sub_perform_create(self, serializer):
        occupationsys_id = self.request.data.get('occupationsys_id', None)
        if occupationsys_id is None:
            raise exceptions.NotAcceptable(OccupationError.OCCUPATION_IS_NOT_EXIST)
        serializer.save(
            user=self.request.user,
            occupation_id=occupationsys_id
        )
        return True

    def sub_perform_update(self, serializer):
        occupationsys_id = self.request.data.get('occupationsys_id', None)
        if occupationsys_id is None:
            raise exceptions.NotAcceptable(OccupationError.OCCUPATION_IS_NOT_EXIST)
        serializer.save(occupation_id=occupationsys_id)
        return True
