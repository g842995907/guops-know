# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from common_framework.utils.rest.routers import get_default_router
from course_occupation.web.view import index_occupation, get_occuption_data, bubblechar, index_ad, line_chart
from course_occupation.web import viewset

viewsets = (
    viewset.OccupationSystemViewSet,
    viewset.OccupationIsChoiceViewSet,
)

router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),

    url(r'^index_occupation/$', index_occupation, name='index_occupation'),
    url(r'^get_occuption_data/$', get_occuption_data, name='get_occuption_data'),
    url(r'^bubblechar/$', bubblechar, name='bubblechar'),
    url(r'^line_chart/$', line_chart, name='line_chart'),

    #ad
    url(r'^index_ad/$', index_ad, name='index_ad'),
]
