# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from common_framework.utils.rest.routers import get_default_router

from x_vulns import api
from x_vulns import views


viewsets = (
    api.ExtNvdViewSet,
    api.ExtCvenvdViewSet,
    api.ExtCnnvdViewSet,
    api.ExtEdbViewSet
)

router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),
]


urlpatterns += [
	url(r'^list/$', views.vuln_list, name='vuln_list'),
    url(r'^global/$', views.vuln_global, name='vuln_global'),

    url(r'^list/(?P<pk>{pk_pattern})/$'.format(pk_pattern=api.LOOKUP_VALUE_REGEX), views.vuln_detail, name='vuln_detail'),

    url(r'^api/list/$', views.api_vuln_list, name='api_vuln_list'),
    url(r'^api/list/(?P<pk>{pk_pattern})/$'.format(pk_pattern=api.LOOKUP_VALUE_REGEX), views.api_vuln_detail, name='api_vuln_detail'),
    url(r'^api/global_risk/$', views.api_vuln_global_risk, name='api_vuln_global_risk'),
    url(r'^api/global_type/$', views.api_vuln_global_type, name='api_vuln_global_type'),
    url(r'^api/global_time/$', views.api_vuln_global_time, name='api_vuln_global_time'),

]
