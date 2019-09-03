import logging

from rest_framework import filters
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets

from common_framework.utils.constant import Status
from common_framework.utils.rest.mixins import CacheModelMixin, DestroyModelMixin, PublicModelMixin
from common_framework.utils.rest.request import RequestData

from x_tools.models import Tool, ToolCategory, ToolComment
from x_tools.serializers import ToolSerializer, ToolCategorySerializer, ToolCommentSerializer


LOG = logging.getLogger(__name__)


class ToolViewSet(CacheModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Tool.objects.filter(status=Status.NORMAL)
    serializer_class = ToolSerializer
    permission_classes = (IsAuthenticated, )
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name', 'introduction')
    ordering_fields = ('id', 'lock')
    ordering = ('lock', '-id', )

    def get_queryset(self):
        queryset = self.queryset

        data = RequestData(self.request, is_query=True)
        category = data.get('search_category')
        if category:
            queryset = queryset.filter(category__contains=category)
            for tool in queryset:
                tool_categoy = tool.category
                if category not in tool_categoy.split(","):
                    queryset = queryset.exclude(id=tool.id)

        platforms = data.get('search_platforms')
        if platforms is not None:
            queryset = queryset.filter(platforms__contains=platforms)

        license_model = data.get('search_license_model')
        if license_model:
            queryset = queryset.filter(license_model=license_model)

        return queryset


class WebToolViewSet(ToolViewSet):
    def get_queryset(self):
        queryset = super(WebToolViewSet, self).get_queryset()
        return queryset.filter(public=True)


class ToolCategoryViewSet(CacheModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ToolCategory.objects.all()
    serializer_class = ToolCategorySerializer
    permission_classes = (IsAuthenticated, )
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('cn_name', 'en_name')
    ordering_fields = ('id', )
    ordering = ('id', )
