# -*- coding: utf-8 -*-
from itertools import groupby

from django.db.models import Count
from rest_framework import exceptions, status
from rest_framework import filters, viewsets
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common_framework.utils.constant import Status
from common_framework.utils.rest import filter as common_filters
from common_framework.utils.rest import mixins as common_mixins
from common_framework.utils.rest.request import RequestData
from course.models import Lesson
from course_occupation.cms.serializers import OccupationSerializer, OccupationCourseSerializer
from course_occupation.models import OccupationSystem, OccupationLink, OccupationCourse, OccupationIsChoice
from course_occupation.response import OccupationError


class OccupationViewSet(common_mixins.CacheModelMixin,
                        common_mixins.PublicModelMixin,
                        common_mixins.DestroyModelMixin,
                        common_mixins.AuthsMixin,
                        viewsets.ModelViewSet):
    queryset = OccupationSystem.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = OccupationSerializer

    filter_backends = (filters.SearchFilter, common_filters.BootstrapOrderFilter)
    ordering_fields = ('update_time', 'name')
    search_fields = ('name',)

    def sub_perform_create(self, serializer):
        if serializer.validated_data.has_key('name'):
            if serializer.validated_data.get('name') == '':
                raise exceptions.ValidationError({'name': [OccupationError.NAME_REQUIRED]})

        instance = serializer.save()
        advanced_name_id_list = self.request.POST.getlist('advanced_name')
        name_list = []
        for i, advanced in enumerate(advanced_name_id_list):
            occupation_links = OccupationLink(
                occupation_id=instance.id,
                advanced_id=int(advanced)
            )
            name_list.append(occupation_links)
        OccupationLink.objects.bulk_create(name_list)
        return True

    def sub_perform_update(self, serializer):
        if serializer.validated_data.has_key('name'):
            if serializer.validated_data.get('name') == '':
                raise exceptions.ValidationError({'name': [OccupationError.NAME_REQUIRED]})
            elif OccupationSystem.objects.filter(name=serializer.validated_data.get('name')).exists():
                raise exceptions.ValidationError({'name': [OccupationError.NAME_HAVE_EXISTED]})
        if serializer.validated_data.get('public') is None:
            serializer.validated_data['public'] = False

        instance = serializer.save()
        advanced_name_id_list = self.request.POST.getlist('advanced_name')
        name_list = []
        OccupationLink.objects.filter(occupation=instance).delete()  # 先删除已经存在的进阶职位
        for i, advanced in enumerate(advanced_name_id_list):
            instance_advanced = OccupationSystem.objects.get(pk=int(advanced))
            occupation_links = OccupationLink(
                occupation=instance,
                advanced=instance_advanced
            )
            name_list.append(occupation_links)
        OccupationLink.objects.bulk_create(name_list)
        return True

    def perform_batch_destroy(self, queryset):
        # 判断职业已经被用户使用， 就无法进行删除
        choice_ids = []
        is_choice_queryset = OccupationIsChoice.objects.all().values('occupation')
        for choice_queryser in is_choice_queryset:
            choice_ids.append(choice_queryser['occupation'])
        if queryset.filter(id__in=choice_ids).exists():
            raise exceptions.NotAcceptable(OccupationError.OCCUPATION_IS_USING_BY_USER)
        return super(OccupationViewSet, self).perform_batch_destroy(queryset)

    def get_queryset(self):
        queryset = self.queryset
        data = RequestData(self.request, is_query=True)
        search_difficulty = data.get('search_difficulty', int)
        if search_difficulty is not None:
            queryset = queryset.filter(difficulty=search_difficulty)

        return queryset

    def extra_handle_list_data(self, data):
        """
        处理职业体系列表页面课时数的显示
        """
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
        occupation_course_list = groupby(occupation_courses, key=lambda x: x['occupation_system_id'])  #根据职业id对课程进行分组
        occupation_course_list = dict([(key, [a for a in group]) for key, group in occupation_course_list])
        lesson_list = Lesson.objects.filter(status=Status.NORMAL).filter(course__id__in=course_id_list).values('course_id').annotate(
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

    @list_route(methods=['get', ])
    def get_advanced_names(self, request):
        # 进阶的职位，和职位难度相互制约，寻找大于当前职位难度的职位 # 新增， 分组显示，显示所有难度大于1的进阶职位
        difficulty = request.query_params.get('difficulty', '1')
        get_advanced_names = self.get_serializer(OccupationSystem.objects.filter(difficulty__gt=int(difficulty)), many=True).data
        return Response(data=get_advanced_names, status=status.HTTP_200_OK)
        pass


class OccupationCourseViewSet(common_mixins.CacheModelMixin,
                              common_mixins.DestroyModelMixin,
                              common_mixins.AuthsMixin,
                              common_mixins.ObligatoryModelMixin,
                              viewsets.ModelViewSet):
    queryset = OccupationCourse.objects.filter(status=Status.NORMAL)
    permission_classes = (IsAuthenticated,)
    serializer_class = OccupationCourseSerializer

    filter_backends = (filters.SearchFilter, common_filters.BootstrapOrderFilter)
    ordering_fields = ('update_time', 'course_count', 'course_name')
    search_fields = ('course__name',)

    def get_queryset(self):
        queryset = self.queryset
        data = RequestData(self.request, is_query=True)
        occupationsystem_id = data.get('occupation_id', int)
        if occupationsystem_id is not None:
            queryset = queryset.filter(occupation_system=occupationsystem_id)

        direction = data.get('search_direction', int)
        if direction is not None:
            queryset = queryset.filter(course__direction=direction)

        sub_direction = data.get('search_sub_direction', int)
        if sub_direction is not None:
            queryset = queryset.filter(course__sub_direction=sub_direction)

        lesson_table = Lesson._meta.db_table
        queryset = queryset.extra(
            select={
                'course_count': '''
                                      SELECT COUNT(*) from {lesson_table} WHERE 
                                      {lesson_table}.course_id = {course_table}.course_id AND 
                                      {lesson_table}.status = {lesson_status}
                                    '''.format(
                    lesson_table=lesson_table,
                    course_table=queryset.model._meta.db_table,
                    lesson_status=Status.NORMAL
                )
            }
        )

        return queryset
