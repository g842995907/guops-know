from django.conf.urls import url, include
from cloud_client.cms import views, viewset
from common_framework.utils.rest.routers import get_default_router

viewsets = (
    viewset.UpdateViewSet,
)

router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),

    url(r'^update/$', views.update, name='update'),
    url(r'^update/(?P<update_id>[a-z|0-9]+)/$', views.update_detail, name='update_detail'),
]
