from django.conf.urls import url, include

from common_cloud.web import views
from common_cloud.web import viewset
from common_framework.utils.rest.routers import get_default_router

viewsets = (
    viewset.UpdateViewSet,
)

router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),
    url(r'^comment/', include([
        url(r'^list/$', views.list_comment, name='list'),
        url(r'^create/$', views.post_comment, name='create'),
        url(r'^delete/$', views.delete_comment, name='delete'),
        url(r'^likes/$', views.like_list, name='likes'),
        url(r'^status/$', views.like_status, name='status'),
    ], namespace='comment')),

    url(r'^update_list/$', views.update_list, name='update_list'),
]
