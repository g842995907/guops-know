# -*-coding: utf-8 -*-
from django.urls import reverse
from django.utils.translation import gettext as _
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from common_auth.api import oj_auth_class
from common_framework.utils.constant import Status
from common_framework.utils.rest import mixins as common_mixins
from common_framework.utils.rest.request import RequestData
from common_calendar import api as calendar_api

from practice_experiment.cms import serializers
from practice_experiment.models import Direction, Experiment


class DirectionViewSet(common_mixins.CacheModelMixin,
                       viewsets.ReadOnlyModelViewSet):
    queryset = Direction.objects.filter(status=Status.NORMAL)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.DirectionSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('last_edit_time',)
    ordering = ('last_edit_time',)


class ExperimentViewSet(common_mixins.CacheModelMixin,
                    viewsets.ReadOnlyModelViewSet):
    queryset = Experiment.objects.filter(status=Status.NORMAL).filter(public=True)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ExperimentSerializer

    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('id',)
    ordering = ('-id',)
    search_fields = ('name',)

    @oj_auth_class
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
