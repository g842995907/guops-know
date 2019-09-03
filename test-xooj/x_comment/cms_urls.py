from django.conf.urls import url, include

from common_framework.utils.rest.routers import get_default_router

from x_comment import cms_views
from x_comment.cms import viewset


viewsets = (
    viewset.CommentViewSet,
)

router = get_default_router(viewsets)

urlpatterns = [
    url(r'^comments/$', cms_views.comment_list, name='comment_list'),
]

urlpatterns += [
    url(r'^api/', include(router.urls, namespace='api')),
]
