# -*- coding: utf-8 -*-
from rest_framework import filters
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common_framework.utils.rest.mixins import CacheModelMixin

from x_vulns.models import ExtCvenvd, ExtCnnvd, ExtEdb, ExtNvd
from x_vulns.serializers import ExtCvenvdSerializer, ExtCnnvdSerializer, ExtEdbSerializer, ExtNvdSerializer


LOOKUP_VALUE_REGEX = '[0-9\nA-Z|-]+'


# 合并 viewset
class ExtNvdViewSet(CacheModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ExtNvd.objects.all()
    serializer_class = ExtNvdSerializer
    permission_classes = (IsAuthenticated, )
    lookup_value_regex = LOOKUP_VALUE_REGEX
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('id', 'summary', )
    ordering_fields = ('edit_time', 'pub_date', )
    ordering = ('edit_time', '-pub_date', )
    page_cache_age = 3600 * 24


class ExtCvenvdViewSet(CacheModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ExtCvenvd.objects.all()
    serializer_class = ExtCvenvdSerializer
    permission_classes = (IsAuthenticated, )
    lookup_value_regex = LOOKUP_VALUE_REGEX
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('summary', )
    ordering_fields = ('pub_date', )
    ordering = ('-pub_date', )
    page_cache_age = 3600 * 24


class ExtCnnvdViewSet(CacheModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ExtCnnvd.objects.all()
    serializer_class = ExtCnnvdSerializer
    permission_classes = (IsAuthenticated, )
    lookup_value_regex = LOOKUP_VALUE_REGEX
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('summary',)
    ordering_fields = ('pub_date', )
    ordering = ('-pub_date', )
    page_cache_age = 3600 * 24


class ExtEdbViewSet(CacheModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ExtEdb.objects.all()
    serializer_class = ExtEdbSerializer
    permission_classes = (IsAuthenticated, )
    lookup_value_regex = LOOKUP_VALUE_REGEX
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('v_name',)
    ordering_fields = ('pub_date', )
    ordering = ('-pub_date', )
    page_cache_age = 3600 * 24