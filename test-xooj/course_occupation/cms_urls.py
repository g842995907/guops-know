# -*- coding: utf-8 -*-
from course_occupation.cms import views, viewset
from common_framework.utils.rest.routers import get_default_router

from django.conf.urls import url, include

viewsets = (
    viewset.OccupationViewSet,
    viewset.OccupationCourseViewSet,
)
router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),
    url(r'^occupation_list/$', views.occupation_list, name='occupation_list'),
    url(r'^occupation_detail/(?P<occupation_id>[a-z|0-9]+)/$', views.occupation_detail, name='occupation_detail'),

    url(r'^occupation_course_list/(?P<occupation_id>[a-z|0-9]+)/$', views.occupation_course_list,
        name='occupation_course_list'),

    url(r'^add_occupation_course/(?P<occupation_id>[a-z|0-9]+)/$', views.add_occupation_course,
        name='add_occupation_course'),

    url(r'^occupation_difficult/$', views.occupation_difficult, name='occupation_difficult'),

]
