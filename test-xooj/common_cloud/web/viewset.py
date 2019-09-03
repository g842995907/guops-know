# -*- coding: utf-8 -*-

from rest_framework import filters, mixins
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet

from common_cloud import models as cloud_models
from common_cloud.web import serializers
from common_framework.utils.constant import Status


class UpdateViewSet(ReadOnlyModelViewSet, ):
    queryset = cloud_models.UpdateInfo.objects.filter(status=Status.NORMAL)
    permission_classes = (AllowAny,)
    serializer_class = serializers.UpdateSerializer
    related_cache_class = ()

    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('id',)
    ordering = ('-id',)
    search_fields = ('name',)
