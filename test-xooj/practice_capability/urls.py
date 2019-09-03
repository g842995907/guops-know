from django.conf.urls import url, include

from common_framework.utils.rest.routers import get_default_router
from practice_capability.web import viewset
from practice_capability.web import views

viewsets = (
   viewset.TestPaperViewSet,
)

router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),
    url(r'^exam/$', views.exam, name='exam'),
    url(r'^exam_detail/(?P<testpaper_id>[a-z|0-9]+)/$', views.exam_detail, name='exam_detail'),
]
