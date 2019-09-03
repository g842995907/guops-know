# -*- coding: utf-8 -*-
import logging

from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response

from common_auth.models import User
from common_framework.utils.cache import CacheProduct, delete_cache, cache_wrapper
from common_framework.utils.rest.mixins import CacheModelMixin
from common_message.models import Message
from common_message.serializer import MessageSerializer


MESSAGE_TYPE_SYSTEM = 0
MESSAGE_TYPE_APP = 1

_cache_instance = CacheProduct("common_message")

logger = logging.getLogger(__name__)


def get_users(user, faculty, major, classes, team):
    users = []
    if not user:
        queryset = User.objects.filter()
        if team:
            queryset |= queryset.filter(team=team)

        if major:
            queryset |= queryset.filter(major=major)

        if faculty:
            queryset |= queryset.filter(faculty=faculty)

        if classes:
            queryset |= queryset.filter(classes=classes)

        for u in queryset:
            users.append(u)
    else:
        users.append(user)

    return users


def add_message(title, content, url, message_type=MESSAGE_TYPE_SYSTEM, user=None,
                faculty=None, major=None, classes=None, team=None):
    '''
        新增一个消息, 
        content: 消息内容,
        message_type: 消息类型,0系统消息, 1应用活动消息
        user: 发送的对象
        faculty: 院信息
        major: 年级信息
        classes: 班级信息
        team: 队伍信息
    '''

    users = get_users(user, faculty, major, classes, team)
    logger.info("new message[%s] send to user count[%d] url[%s]", content, len(users), url)

    for u in users:
        Message.objects.create(
            content=content,
            user=u,
            url=url,
            message_type=message_type,
        )

    delete_cache(_message_cache_instance)
    delete_cache(_cache_instance)


def delete_message(title, content, url, message_type=MESSAGE_TYPE_SYSTEM, user=None,
                   faculty=None, major=None, classes=None, team=None):
    users = get_users(user, faculty, major, classes, team)
    logger.info("delete message[%s] from user count[%d] url[%s]", content, len(users), url)

    for u in users:
        message = Message.objects.filter(
            content=content,
            user=u,
            url=url,
            message_type=message_type,
        ).first()
        if message:
            message.read = True
            message.save()

    delete_cache(_message_cache_instance)
    delete_cache(_cache_instance)



@api_view()
def get_unread_message_count(request):
    """
        获取某个用户未读信息个数
    """
    count = Message.objects.filter(user=request.user, read=False).count()
    return Response({'count': count})


def _generate_cache_key(view):
    return "%s:%d:%d:%d" % (
        view.__class__.__name__,
        view.paginator.offset,
        view.paginator.limit,
        view.request.user.id)


class MessageViewSet(CacheModelMixin, ReadOnlyModelViewSet):
    serializer_class = MessageSerializer
    permisson_classes = (IsAuthenticated,)
    generate_cache_key = _generate_cache_key

    def get_queryset(self):
        return Message.objects.filter(user=self.request.user, read=False).order_by("create_time")


_message_cache_instance = CacheProduct(MessageViewSet.__name__)
