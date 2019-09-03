# coding:utf-8
import logging

from rest_framework import filters
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from common_framework.utils.constant import Status
from common_framework.utils.rest.mixins import CacheModelMixin, DestroyModelMixin, PublicModelMixin
from common_framework.utils.rest.request import RequestData

from x_comment.models import Comment
from x_comment.serializers import CommentSerializer
from practice_real_vuln.models import RealVulnTask
from rest_framework.decorators import list_route, detail_route
from rest_framework import exceptions, status, response, viewsets
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from practice_exercise.models import PracticeExerciseTask

practice_types = {}


class CommentViewSet(CacheModelMixin, DestroyModelMixin,
                     PublicModelMixin, viewsets.ModelViewSet):
    queryset = Comment.objects.filter(status=Status.NORMAL)
    serializer_class = CommentSerializer
    permission_classes = (AllowAny,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('username', 'comment')
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)
    pt = settings.PLATFORM_TYPE

    def get_queryset(self):
        queryset = self.queryset
        data = RequestData(self.request, is_query=True)
        if self.pt == "OJ":
            queryset = queryset.exclude(resource__endswith="tool")
        elif self.pt == "AD":
            queryset = queryset.filter(resource__endswith="tool")
        tenant = data.get('search_tenant')
        if tenant:
            queryset = queryset.filter(tenant__contains=tenant)

        resource = data.get('search_type')
        if resource == "0":
            queryset = queryset.filter(resource__endswith="course")
        elif resource == "1":
            queryset = queryset.filter(resource__endswith="tool")
        elif resource == "2":
            queryset = queryset.filter(resource__endswith=".1")
        elif resource == "3":
            queryset = queryset.filter(resource__endswith=".2")

        comment = data.get('search_comment')
        if comment:
            queryset = queryset.filter(theme_name__contains=comment)

        root_page = data.get('search_parent')
        if not root_page:
            queryset = queryset.filter(parent_id__isnull=True)
        else:
            if root_page == "0":
                queryset = queryset.filter(parent_id__isnull=True)
            elif root_page == "1":
                root_idx = data.get("parent")
                if root_idx:
                    queryset = queryset.filter(parent_id=root_idx)
                else:
                    queryset = queryset.filter(parent_id__isnull=False)

        parent_ids = data.get("parent_ids")
        if parent_ids:
            queryset = queryset.filter(parent_id=parent_ids)
        return queryset

    def extra_handle_list_data(self, data):
        for row in data:
            resource = row['resource']
            category = resource.split(".")[1]
            row.update({
                "operating": row['comment']
            })
            if category == "course" and settings.PLATFORM_TYPE != 'AD':
                from course.models import Course
                result = Course.objects.filter(hash=resource)
                for task in result:
                    row.update({
                        "theme": "[{}]".format(_("x_course")) + task.name
                    })
            elif category == "tool" and settings.PLATFORM_TYPE != 'OJ':
                from x_tools.models import Tool
                result = Tool.objects.filter(hash=resource)
                for task in result:
                    row.update({
                        "theme": "[{}]".format(_("x_tool")) + task.name
                    })
            else:
                if settings.PLATFORM_TYPE != "AD":
                    if len(RealVulnTask.objects.filter(hash=resource)) != 0:
                        result = RealVulnTask.objects.filter(hash=resource)
                        for task in result:
                            row.update({
                                "theme": "[{}]".format(_("x_real_vuln")) + task.title
                            })
                    elif len(PracticeExerciseTask.objects.filter(hash=resource)) != 0:
                        result = PracticeExerciseTask.objects.filter(hash=resource)
                        for task in result:
                            row.update({
                                "theme": "[{}]".format(_("x_exercise")) + task.title
                            })
        return data

    @detail_route(methods=['post'])
    def reply_comment(self, request, pk):  # 回复按钮
        params = request.POST
        try:
            logo = request.user.logo.url
        except:
            logo = ""
        if params.get('parent') != "null":
            parents = params.get('parent')
        else:
            parents = pk
        comments = escape(params.get("comment"))
        create_params = {
            'username': request.user.username,
            'nickname': request.user.nickname,
            'avatar': logo,
            'resource': params.get("hash"),
            'comment': comments,
        }
        create_params['parent_id'] = parents
        Comment.objects.create(**create_params)
        self.clear_cache()
        return response.Response({'status': 0})

    @list_route(methods=['delete'], )  # 删除主贴，关联删除跟帖
    def batch_destroy(self, request):
        ids = request.data.getlist('ids', [])
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)
        queryset = self.queryset.filter(id__in=ids)
        if hasattr(self, 'clear_cache') and self.perform_batch_destroy(queryset):
            self.clear_cache()
        queryset_sun = self.queryset.filter(parent__in=ids)
        if hasattr(self, 'clear_cache') and self.perform_batch_destroy(queryset_sun):
            self.clear_cache()
        return Response(status=status.HTTP_204_NO_CONTENT)
