# -*- coding: utf-8 -*-
import logging

from rest_framework import filters, response, status
from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from rest_framework.decorators import list_route
from django.http import JsonResponse, HttpResponse
from django.urls import reverse

from common_framework.utils.constant import Status
from common_framework.utils.rest.mixins import CacheModelMixin, DestroyModelMixin
from common_framework.utils.rest.request import RequestData
from common_framework.utils.rest.list_view import list_view

from practice_exercise.models import PracticeExerciseTask
from practice_real_vuln.models import RealVulnTask

from x_comment.models import Comment, NewLikes
from x_comment.serializers import CommentSerializer, CommentSerializerLike, CommentListViewSerializer
from django.conf import settings
import urllib

logger = logging.getLogger(__name__)


class CommentViewSet(CacheModelMixin, DestroyModelMixin,
                     viewsets.ModelViewSet):
    queryset = Comment.objects.filter(status=Status.NORMAL).filter(public=True)
    serializer_class = CommentSerializer
    permission_classes = (AllowAny,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('tenant', 'username', 'resource', 'comment')
    ordering_fields = ('create_time',)
    ordering = ('create_time',)

    def get_queryset(self):
        queryset = self.queryset

        data = RequestData(self.request, is_query=True)
        tenant = data.get('search_tenant')
        if tenant:
            queryset = queryset.filter(tenant__contains=tenant)

        username = data.get('search_username')
        if username:
            queryset = queryset.filter(username__contains=username)

        resource = data.get('search_resource')
        if resource is not None:
            queryset = queryset.filter(resource__contains=resource)

        comment = data.get('search_comment')
        if comment:
            queryset = queryset.filter(comment__contains=comment)

        return queryset

    @list_route(methods=['get'], )
    def get_ask(self, request):
        queryset = self.queryset
        states = self.request.query_params['states']
        states = int(states)
        user = request.user
        queryset = queryset.filter(username=user)
        queryset = queryset.filter(parent__isnull=states)
        # total = len(queryset)

        ask_list = []
        for row in queryset:
            resource = row.resource
            category = resource.split(".")[1]
            title = ''
            # 页面跳转链接
            resource_url = ''
            if category == "course" and settings.PLATFORM_TYPE != 'AD':
                from course.models import Course
                result = Course.objects.filter(hash=resource)
                for task in result:
                    title = task.name
                    resource_url = reverse('course:detail', args=(task.id,))
            elif category == "tool" and settings.PLATFORM_TYPE != 'OJ':
                from x_tools.models import Tool
                result = Tool.objects.filter(hash=resource)
                for task in result:
                    title = task.name
                    resource_url = reverse('x_tools:detail', args=(task.id,))
            elif category == "lesson" and settings.PLATFORM_TYPE != "AD":
                from course.models import Lesson
                result = Lesson.objects.filter(hash=resource)
                for task in result:
                    title = task.name
                    resource_url = reverse('course:markdown_new') + "?" + urllib.urlencode({'course_screen':'one_screen', 'lesson_id':task.id})
            else:
                if settings.PLATFORM_TYPE != "AD":
                    if len(RealVulnTask.objects.filter(hash=resource)) != 0:
                        result = RealVulnTask.objects.filter(hash=resource)
                        for task in result:
                            title = task.title
                            if title == [] or title == None:
                                title = task.theme_name
                            resource_url = reverse('practice:defensetraintask', args=(category, resource))
                    elif len(PracticeExerciseTask.objects.filter(hash=resource)) != 0:
                        result = PracticeExerciseTask.objects.filter(hash=resource)
                        for task in result:
                            title = task.title
                            if title == [] or title == None:
                                title = task.theme_name
                            resource_url = reverse('practice:defensetraintask', args=(category, resource))
            ask_dict = {
                'id': row.id,
                'title': title,
                'comment': row.comment,
                'last_update': row.update_time,
                'resource_url': resource_url
            }
            ask_list.append(ask_dict)

        return list_view(request, ask_list, CommentListViewSerializer)
        # return response.Response({'total': total, 'rows': ask_list}, status=status.HTTP_200_OK)


class CommentLikeViewSet(CacheModelMixin, DestroyModelMixin,
                         viewsets.ModelViewSet):
    queryset = NewLikes.objects.filter(status=Status.NORMAL)
    serializer_class = CommentSerializerLike
    permission_classes = (AllowAny,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('username_id', 'status')
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)

    def get_queryset(self):
        queryset = self.queryset
        data = RequestData(self.request)
        resource = data.get('resource')
        if resource:
            queryset = queryset.filter(resource__contains=resource)
        username_id = data.get('username_id')
        if username_id:
            queryset = queryset.filter(username_id__contains=username_id)

        return queryset

    def create(self, validated_data):
        comment = self.request.data.get("comment", None)
        username_id = self.request.data.get("username_id", None)
        username = self.request.data.get('username', None)
        resource = self.request.data.get('resource', None)
        ret = {'status': 0, 'msg': '', 'comment': comment}
        comments = Comment.objects.get(id=comment)
        likenum = Comment.objects.get(pk=comment).thumbs_up

        params = dict(comment=comment, username_id=username_id)
        try:
            new_likes = NewLikes.objects.get(**params)
            if new_likes.status == 1:
                likenum = likenum - 1
                Comment.objects.filter(pk=comment).update(thumbs_up=likenum)
                NewLikes.objects.filter(**params).update(status=0)
                ret['status'] = 0
                likenum = "999+" if likenum > 999 else likenum
                ret['msg'] = likenum
            else:
                likenum = likenum + 1
                Comment.objects.filter(pk=comment).update(thumbs_up=likenum)
                NewLikes.objects.filter(**params).update(status=1)
                ret['status'] = 1
                likenum = "999+" if likenum > 999 else likenum
                ret['msg'] = likenum

        except:
            likenum = likenum + 1
            instance = NewLikes.objects.create(
                comment=comments,
                username_id=username_id,
                username=username,
                resource=resource
            )
            instance.save()
            Comment.objects.filter(pk=comment).update(thumbs_up=likenum)
            ret['status'] = 1
            likenum = "999+" if likenum > 999 else likenum
            ret['msg'] = likenum

        self.clear_cache()

        return JsonResponse(ret)
