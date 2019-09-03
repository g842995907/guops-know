from django.conf.urls import url, include

from common_message import views
from common_message.api import MessageViewSet
from common_message import api

urlpatterns = [
    url(r'api/list/$', MessageViewSet.as_view({'get': 'list'})),
    url(r'api/count/$', api.get_unread_message_count),
    url(r'list/$', views.list, name='list')
]

