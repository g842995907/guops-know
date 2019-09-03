from django.conf.urls import url

import views

urlpatterns = [
    url(r'^list/$', views.web_event_list, name='index'),
    url(r'^task_list/$', views.task_list, name='task_list'),
    url(r'^task_list/(?P<event_id>[0-9]+)$', views.task_list, name='task_list'),
    url(r'^do_task/$', views.do_task, name='do_task'),
    url(r'^do_task2/$', views.do_task2, name='do_task2'),
]

