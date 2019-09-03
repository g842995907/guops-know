# -*- coding: utf-8 -*-
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from common_framework.utils.constant import Status
from common_framework.utils.rest import mixins as common_mixins
from common_framework.utils.rest.request import RequestData

from practice_experiment.cms import serializers
from practice_experiment import models as experiment_models
from practice_experiment.web import viewset as web_viewsets


class DirectionViewSet(common_mixins.CacheModelMixin,
                       common_mixins.DestroyModelMixin,
                       viewsets.ModelViewSet):
    queryset = experiment_models.Direction.objects.filter(status=Status.NORMAL)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.DirectionSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('cn_name',)
    ordering = ('cn_name',)
    search_fields = ('cn_name', 'en_name',)

    def sub_perform_destroy(self, instance):
        instance.status = Status.DELETE
        instance.save()
        return True


class ExperimentViewSet(common_mixins.CacheModelMixin,
                    common_mixins.PublicModelMixin,
                    common_mixins.DestroyModelMixin,
                    common_mixins.AuthsMixin,
                    viewsets.ModelViewSet):
    queryset = experiment_models.Experiment.objects.filter(status=Status.NORMAL)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ExperimentSerializer
    related_cache_class = (web_viewsets.ExperimentViewSet,)

    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)
    search_fields = ('name',)

    def sub_perform_create(self, serializer):
        serializer.save(
            last_edit_user=self.request.user,
            creater=self.request.user
        )
        return True

    def sub_perform_destroy(self, instance):
        instance.status = Status.DELETE
        instance.save()
        return True

    def sub_perform_update(self, serializer):
        if serializer.validated_data.get('public') is None:
            serializer.validated_data['public'] = False

        serializer.save()
        return True

    def get_queryset(self):
        queryset = self.queryset

        data = RequestData(self.request, is_query=True)
        direction = data.get('search_direction', int)
        if direction is not None:
            queryset = queryset.filter(direction=direction)

        difficulty = data.get('search_difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        return queryset

    def get_faculty_major_objs(self, request, course_id, faculty=None, major=None):
        if not course_id:
            return []

        course = experiment_models.Experiment.objects.filter(id=course_id).first()
        if not course:
            return []

        return course
