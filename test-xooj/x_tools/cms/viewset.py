# -*- coding: utf-8 -*-
import logging

from rest_framework import exceptions
from rest_framework import filters
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common_framework.utils.constant import Status
from common_framework.utils.rest import filter as common_filters
from common_framework.utils.rest.mixins import CacheModelMixin, DestroyModelMixin, PublicModelMixin
from common_framework.utils.rest.permission import IsStaffPermission
from common_framework.utils.rest.request import RequestData
from practice_real_vuln.response import TaskResError
from x_tools.models import Tool, ToolCategory, ToolComment
from x_tools.response import TaskCategoryError
from x_tools.serializers import ToolSerializer, ToolCategorySerializer, ToolCommentSerializer

LOG = logging.getLogger(__name__)


class RealDestroyModelMixin(DestroyModelMixin):
    def perform_batch_destroy(self, queryset):
        queryset.delete()
        return True


class LockModelMixin(object):
    @list_route(methods=['patch'], )
    def batch_public(self, request):
        ids = request.data.getlist('ids', [])
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        public = int(request.data.get('lock', 0))

        queryset = self.queryset.filter(id__in=ids)
        if hasattr(self, 'clear_cache') and self.perform_batch_public(queryset, public):
            self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_batch_public(self, queryset, lock):
        if queryset.update(lock=lock) > 0:
            return True
        return False


class ToolViewSet(CacheModelMixin, DestroyModelMixin,
                  PublicModelMixin, viewsets.ModelViewSet):
    queryset = Tool.objects.filter(status=Status.NORMAL)
    serializer_class = ToolSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, common_filters.BootstrapOrderFilter)
    search_fields = ('name', 'introduction')
    ordering_fields = ('id', 'name', 'update_time', 'license_model', 'public')
    ordering = ('-id', )

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

    def perform_create(self, serializer):
        if not serializer.validated_data.has_key('name'):
            raise exceptions.ValidationError({'name': [TaskResError.REQUIRED_FIELD]})
        knowledges = None
        if self.request.data.getlist('knowledges'):
            knowledges = self.request.data.getlist('knowledges', [])
            knowledges = [x for x in knowledges if x != '']
            knowledges = ",".join(knowledges)
        self.clear_cache()
        serializer.save(
            create_user=self.request.user,
            knowledges=knowledges,
        )

    def sub_perform_update(self, serializer):
        knowledges = None
        if self.request.data.getlist('knowledges'):
            knowledges = self.request.data.getlist('knowledges', [])
            knowledges = [x for x in knowledges if x != '']
            knowledges = ",".join(knowledges)

        serializer.save(
            knowledges=knowledges,
        )
        return True

class ToolCategoryViewSet(CacheModelMixin, RealDestroyModelMixin,
                          viewsets.ModelViewSet):
    queryset = ToolCategory.objects.all()
    serializer_class = ToolCategorySerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('cn_name', 'en_name')
    ordering_fields = ('id', )
    ordering = ('id', )

    def sub_perform_create(self, serializer):
        if serializer.validated_data.has_key('cn_name'):
            if ToolCategory.objects.filter(cn_name=serializer.validated_data['cn_name']).exists():
                raise exceptions.ValidationError({'cn_name': [TaskCategoryError.REPEAT]})
        serializer.save()
        # super(ToolCategoryViewSet, self).perform_create(serializer)
        return True

    def perform_batch_destroy(self, queryset):
        ids = self.request.data.getlist('ids', [])
        has_normal_choiceTask = Tool.objects.filter(category__in=ids, status=Status.NORMAL)
        if has_normal_choiceTask:
            raise exceptions.NotAcceptable(TaskCategoryError.TYPE_USEING)
        queryset.delete()
        return True


class ToolCommentViewSet(CacheModelMixin, RealDestroyModelMixin,
                         viewsets.ModelViewSet):
    queryset = ToolComment.objects.all()
    serializer_class = ToolCommentSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('comment', )
    ordering_fields = ('create_time', )
    ordering = ('-create_time', )
