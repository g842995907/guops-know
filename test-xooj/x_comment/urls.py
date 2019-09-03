from django.conf.urls import url, include

from common_framework.utils.rest.routers import get_default_router

from x_comment.web import viewset


viewsets = (
    viewset.CommentViewSet,
    viewset.CommentLikeViewSet,
)

router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),
]
