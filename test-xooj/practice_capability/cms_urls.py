from django.conf.urls import url, include

from common_framework.utils.rest.routers import get_default_router
from practice_capability.cms import viewset
from practice_capability.cms import views

viewsets = (
   viewset.TestPaperViewSet,
   viewset.TestPaperTaskViewSet,
)

router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),

    url(r'^list/$', views.testpaper, name='testpaper'),
    url(r'^testpaper/(?P<testpaper_id>[a-z|0-9]+)/$', views.testpaper_detail, name='testpaper_detail'),
    url(r'^paper/(?P<testpaper_id>[a-z|0-9]+)/$', views.paper_detail, name='paper_detail'),
    url(r'^rest/testpaper/(?P<testpaper_id>[a-z|0-9]+)/$', views.ret_testpaper_detail, name='ret_testpaper_detail'),
    url(r'^rest/testpapernew/(?P<testpaper_id>[a-z|0-9]+)/$', views.handler_task_list, name='handler_task_list'),
    url(r'^rest/getlessonlist/$', views.get_lesson_list, name='get_lesson_list'),
    url(r'^rest/generate_docx/$', views.generate_docx, name='generate_docx'),

    url(r'^share_teacher/(?P<testpaper_id>[a-z0-9]+)/$', views.share_teacher, name='share_teacher'),
]
