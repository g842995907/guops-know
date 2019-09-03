import logging

from django.core.cache import cache
from rest_framework import filters, status
from rest_framework.decorators import list_route
from rest_framework.permissions import AllowAny
from rest_framework import viewsets, exceptions
from rest_framework.response import Response

from common_auth.models import User
from common_framework.utils.constant import Status
from common_framework.utils.rest.mixins import CacheModelMixin, DestroyModelMixin, PublicModelMixin
from common_framework.utils.rest.permission import IsStaffPermission
from common_framework.utils.rest.request import RequestData

from x_note.models import Note
from x_note.serializers import NoteSerializer


class NoteViewSet(CacheModelMixin, DestroyModelMixin,
                  PublicModelMixin, viewsets.ModelViewSet):
    queryset = Note.objects.filter(status=Status.NORMAL)
    serializer_class = NoteSerializer
    permission_classes = (AllowAny, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('username', 'content')
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)

    def get_queryset(self):
        queryset = self.queryset

        data = RequestData(self.request, is_query=True)

        resource = data.get('search_resource')
        if resource is not None:
            queryset = queryset.filter(resource__contains=resource)

        content = data.get('search_content')
        if content:
            queryset = queryset.filter(content__contains=content)

        username = data.get('search_username')
        if username:
            queryset = queryset.filter(user__username__contains=username)

        user_id = data.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        report_require = data.get('report')
        if report_require:
            queryset = queryset.filter(resource__endswith='report')

        return queryset

    def sub_perform_update(self, serializer):
        serializer.save(teacher=self.request.user)
        return True

    @list_route(methods=['post'], )
    def set_score(self, request):
        data = RequestData(self.request, is_query=False)
        user_id = data.get('user_id', int)
        if user_id is None:
            raise exceptions.ValidationError("")
        resource = data.get('hash')
        if resource is None:
            raise exceptions.ValidationError("")
        score = data.get('score', int)
        if score is None:
            score = 0
        note = Note.objects.filter(resource=resource, user_id=user_id).first()
        if note:
            note.score = score
            note.save()
        else:
            Note.objects.create(
                content='',
                user=User.objects.get(id=user_id),
                resource=resource,
                score=score
            )
        cache.clear()
        return Response(status=status.HTTP_204_NO_CONTENT)
