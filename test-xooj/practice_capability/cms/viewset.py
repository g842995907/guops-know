# -*- coding: utf-8 -*-
import uuid

from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import list_route
from rest_framework.response import Response
from common_auth.api import oj_share_teacher
from common_framework.utils.constant import Status
from common_framework.utils.rest import filter as common_filters
from common_framework.utils.rest import mixins as common_mixins
from practice_capability import models as capability_modules
from practice_capability.cms import serializers
from practice_capability.web import viewset as web_viewset
from practice_capability.constant import AppType, TestpaperType
from practice.api import get_task_object

from course import models as course_modules

class TestPaperViewSet(common_mixins.ShareTeachersMixin,
                       common_mixins.CacheModelMixin,
                       common_mixins.DestroyModelMixin,
                       common_mixins.PublicModelMixin,
                       viewsets.ModelViewSet):
    queryset = capability_modules.TestPaper.objects.filter(status=Status.NORMAL)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.TestPaperSerializer
    filter_backends = (filters.SearchFilter, common_filters.BootstrapOrderFilter)
    ordering_fields = ('create_time', 'name', 'task_all_score', 'task_number', 'public')
    ordering = ('-create_time',)
    search_fields = ('name',)
    related_cache_class = (web_viewset.TestPaperViewSet,)

    @oj_share_teacher
    def get_queryset(self):
        queryset = self.queryset
        return queryset

    def perform_batch_destroy(self, queryset):
        for test_paper in queryset:
            test_paper.name = "delete_{}".format(uuid.uuid4())
            test_paper.status = Status.DELETE
            test_paper.save()

        return True

    @list_route(methods=['get'])
    def get_homework(self, request):
        lesson_id =self.query_data.get('lesson', int)
        taskArrary = course_modules.LessonPaperTask.objects.filter(lesson__id=lesson_id,
                                                                 type=course_modules.LessonPaperTask.Type.EXERCISE)

        category = self.query_data.get('category')
        question_type = self.query_data.get('question_type_list', int)

        task_list = []
        for t in taskArrary:
            task = get_task_object(t.task_hash)
            if not task:
                continue
            if self.query_data.get('search'):
                keyword = self.query_data.get('search').strip()
                if int(task.hash.split(".")[-1]) == AppType.THEROY:
                    if keyword in task.content:
                        task = task
                    else:
                        continue
                else:
                    if keyword in task.title:
                        task = task
                    else:
                        continue

            task_filter = None

            if category:
                category_id = category.split("_")[0]
                category_type = category.split("_")[-1]
                if int(category_id) == int(task.category.id) and int(task.hash.split(".")[-1]) == int(category_type):
                    if question_type is not None:
                        if int(question_type) != TestpaperType.OPERATION:
                            if int(task.hash.split(".")[-1]) == AppType.THEROY:
                                if int(question_type) == int(task.multiple):
                                    task_filter = task
                        else:
                            if int(task.hash.split(".")[-1]) != AppType.THEROY:
                                task_filter = task
                    else:
                        task_filter = task
            else:
                if question_type is not None:
                    if int(question_type) != TestpaperType.OPERATION:
                        if int(task.hash.split(".")[-1]) == AppType.THEROY:
                            if int(question_type) == int(task.multiple):
                                task_filter = task
                    else:
                        if int(task.hash.split(".")[-1]) != AppType.THEROY :
                            task_filter = task
                else:
                    task_filter = task

            if task_filter is not None:
                task_list.append(task_filter)
        language = self.request.LANGUAGE_CODE
        rows = [serializers.SerializerNew(task, task.score, language).data for task in task_list]

        return Response({'rows':rows})

    @list_route(methods=['get'])
    def lesson_categories(self,request):
        lesson_id = request.GET.get("lesson_id")

        taskArrary = course_modules.LessonPaperTask.objects.filter(lesson__id=lesson_id, type=course_modules.LessonPaperTask.Type.EXERCISE)
        task_list = []
        lesson_categories_list = []
        for t in taskArrary:
            task = get_task_object(t.task_hash)
            if task.category not in lesson_categories_list:
                lesson_categories_list.append(task.category)
                task_list.append(task)
        rows = [serializers.LessonCategoriesSerializer(task.category, task.hash).data for task in task_list]
        return Response({'rows': rows})

class TestPaperTaskViewSet(common_mixins.RequestDataMixin,
                           viewsets.ReadOnlyModelViewSet):
    queryset = capability_modules.TestPaperTask.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.TestPaperTaskSerializer

    def get_queryset(self):
        queryset = self.queryset

        test_paper = self.query_data.get('test_paper', int)
        if test_paper is not None:
            queryset = queryset.filter(test_paper=test_paper)

        return queryset
