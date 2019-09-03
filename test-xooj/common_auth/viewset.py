# -*- coding: utf-8 -*-
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from common_auth import models as auth_models
from common_auth import serializers

from common_framework.utils.rest import mixins as common_mixins


class FacultyViewSet(common_mixins.CacheModelMixin,
                     viewsets.ModelViewSet):
    queryset = auth_models.Faculty.objects.filter()
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.FacultySerializer

    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('id',)
    ordering = ('-id',)
    search_fields = ('name')


class MajorViewSet(common_mixins.CacheModelMixin,
                   common_mixins.RequestDataMixin,
                   viewsets.ModelViewSet):
    queryset = auth_models.Major.objects.filter()
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.MajorSerializer

    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('id',)
    ordering = ('-id',)
    search_fields = ('name')

    def get_queryset(self):
        queryset = self.queryset
        faculty = self.query_data.get('faculty', int)
        if faculty:
            queryset = queryset.filter(faculty=faculty)

        return queryset
