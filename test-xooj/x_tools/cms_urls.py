from __future__ import unicode_literals
from django.conf.urls import include, url

from common_framework.utils.rest.routers import get_default_router
from x_tools.cms import viewset
from x_tools import cms_views

viewsets = (
    viewset.ToolViewSet,
    viewset.ToolCategoryViewSet,
    viewset.ToolCommentViewSet,
)

router = get_default_router(viewsets)


urlpatterns = [
    url(r'^tools/$', cms_views.tool_list, name='tool_list'),
    url(r'^categories/$', cms_views.category_list, name='category_list'),
    url(r'^comments/$', cms_views.comment_list, name='comment_list'),

    url(r'^image/upload/$', cms_views.upload_image, name='upload_image'),
    url(r'^image/remove/$', cms_views.remove_image, name='remove_image'),
]

urlpatterns += [
    url(r'^api/', include(router.urls, namespace='api')),
]

urlpatterns += [
    url(r'^tools/(?P<tool_id>[^/.]+)/detail/$', cms_views.tool_detail, name='tool_detail'),
    url(r'^tools/create/$', cms_views.tool_create, name='tool_create'),
    url(r'^tools/(?P<tool_id>[^/.]+)/custom_detail/$', cms_views.custom_tool_detail, name='custom_tool_detail'),
    #
    url(r'^categories/(?P<category_id>[^/.]+)/detail/$', cms_views.category_detail, name='category_detail'),
    url(r'^categories/create/$', cms_views.category_create, name='category_create'),
    url(r'^categories/(?P<category_id>[^/.]+)/delete/$', cms_views.category_delete, name='category_delete'),
    #
    url(r'^comments/(?P<comment_id>[^/.]+)/detail/$', cms_views.comment_detail, name='comment_detail'),
    url(r'^comments/create/$', cms_views.comment_create, name='comment_create'),
    url(r'^comments/(?P<comment_id>[^/.]+)/delete/$', cms_views.comment_delete, name='comment_delete'),

]
