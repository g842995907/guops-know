# from django.conf.urls import url, include

from common_cloud.cms import viewset
from common_framework.utils.rest.routers import get_default_router

viewsets = (
    viewset.DepartmentViewSet,
    viewset.UpdateViewSet,
)

router = get_default_router(viewsets)

urlpatterns = [
    # url(r'^api/', include(router.urls, namespace='api')),
    #
    # url(r'^department/$', views.department, name='department'),
    # url(r'^department/(?P<department_id>[a-z|0-9]+)/$',
    # views.department_detail, name='department_detail'),
    #
    # url(r'^update/$', views.update, name='update'),
    # url(r'^update/(?P<update_id>[a-z|0-9]+)/$',
    # views.update_detail, name='update_detail'),
]
