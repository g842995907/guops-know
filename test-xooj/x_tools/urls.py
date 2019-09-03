from django.conf.urls import url, include

from common_framework.utils.rest.routers import get_default_router
from x_tools import views
from x_tools.web import viewset

viewsets = (
    viewset.WebToolViewSet,
    viewset.ToolCategoryViewSet,
)

router = get_default_router(viewsets)


urlpatterns = [
    url(r'^list/$', views.tool_list, name='list'),
    url(r'^detail/(?P<tool_id>[^/.]+)/$', views.tool_detail, name='detail'),
    url(r'^download/(?P<tool_id>[^/.]+)/$', views.tool_download, name='download'),
    url(r'^recommand/$', views.ToolRecommandView.as_view(), name='recommand'),
]

urlpatterns += [
    url(r'^api/', include(router.urls, namespace='api')),
]
