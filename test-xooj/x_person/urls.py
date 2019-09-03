# -*- coding: utf-8 -*-
from django.conf.urls import url, include
from common_framework.utils.rest.routers import get_default_router
from x_person import views
from x_person.web import api
from django.conf import settings

viewsets = (
    api.TeamViewSet,
    api.TeamUserViewSet,
    api.UserViewSet,
    api.FacultyViewSet,
    api.MajorViewSet,
    api.ClassesViewSet,
)

router = get_default_router(viewsets)

urlpatterns = [
    url(r'^info/$', views.info, name='info'),
    url(r'^team/$', views.team, name='team'),
    url(r'^collect/$', views.collect, name='collect'),
    url(r'^rank/$', views.rank, name='rank'),
    url(r'^team/(?P<pk>[0-9]+)/$', views.team_edit, name='team_edit'),
    url(r'^person/$', views.index, name='person'),
    url(r'^join_team/$', views.join_team, name='join_team'),
    url(r'^create_team/$', views.create_team, name='create_team'),
    url(r'^send_validate_email/(?P<user_id>[0-9]+)/$', views.send_validate_email, name='send_validate_email'),
    url(r'^email_validate/(?P<user_id>[0-9]+)/\d+$', views.email_validate, name="email_validate"),
    # url(r'^index_new/$', views.index_new, name='index_new'),
    # url(r'^index_ad/$', views.index_ad, name='index_ad'),
    url(r'^bubblechar/$', views.bubblechar, name='bubblechar'),
]

urlpatterns += [
    url(r'^api/', include(router.urls, namespace='api')),
]

if settings.PLATFORM_TYPE == 'AD':
    urlpatterns += [
        #a d
        url(r'^index_ad/$', views.index_ad, name='index_ad'),
    ]
elif settings.PLATFORM_TYPE == 'OJ':
    urlpatterns += [
        # OJ
        url(r'^index_new/$', views.index_new, name='index_new')
    ]
else:
    urlpatterns += [
        url(r'^index_new/$', views.index_new, name='index_new'),
        url(r'^index_ad/$', views.index_ad, name='index_ad'),
    ]