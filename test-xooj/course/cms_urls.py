from django.conf.urls import url, include

from common_framework.utils.rest.routers import get_default_router

from course.cms import viewset, views

viewsets = (
    viewset.DirectionViewSet,
    viewset.SubDirectionViewSet,
    viewset.CourseViewSet,
    viewset.LessonViewSet,
    viewset.LessonNewViewSet,
    viewset.LessonJstreeViewSet,
    viewset.CourseScheduleViewSet,
    viewset.ClassroomGroupInfoViewSet,
    viewset.ClassroomGroupTemplateViewSet,
)

router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),

    url(r'^direction/$', views.direction, name='direction'),
    url(r'^direction/(?P<direction_id>[a-z|0-9]+)/$', views.direction_detail, name='direction_detail'),

    url(r'^course/$', views.course, name='course'),
    url(r'^course/(?P<course_id>[a-z|0-9]+)/$', views.course_detail, name='course_detail'),
    url(r'^lesson_sort/(?P<course_id>[a-z|0-9]+)/$', views.lesson_sort, name='lesson_sort'),
    url(r'^lesson_sort_new/(?P<course_id>[a-z|0-9]+)/$', views.lesson_sort_new, name='lesson_sort_new'),

    url(r'^experiment/$', views.experiment, name='experiment'),
    url(r'^experiment/(?P<experiment_id>[a-z|0-9]+)/$', views.experiment_detail, name='experiment_detail'),

    url(r'^lesson_list/(?P<course_id>[a-z0-9]+)/$', views.lesson, name='lesson'),
    url(r'^order_lessons/$', views.order_lessons, name='order_lessons'),
    url(r'^lesson/(?P<course_id>[a-z0-9]+)/(?P<lesson_id>[a-z0-9-]+)/$', views.lesson_detail, name='lesson_detail'),
    url(r'^lesson/(?P<lesson_id>[a-z|0-9]+)/custom_detail/$',
        views.custom_lesson_detail, name='custom_lesson_detail'),

    url(r'^exp_lesson_list/(?P<experiment_id>[a-z0-9]+)/$', views.exp_lesson, name='exp_lesson'),
    url(r'^exp_lesson/(?P<experiment_id>[a-z0-9]+)/(?P<lesson_id>[a-z0-9-]+)/$', views.exp_lesson_detail, name='exp_lesson_detail'),

    url(r'^auth_class/(?P<course_id>[a-z0-9]+)/$', views.auth_class, name='auth_class'),
    url(r'^share_teacher/(?P<event_id>[a-z0-9]+)/$', views.share_teacher, name='share_teacher'),

    url(r'^practice_categories/(?P<type_id>[a-z0-9]+)/$', views.practice_categories, name='practice_categories'),

    url(r'^reports/(?P<experiment_id>[a-z0-9]+)/(?P<lesson_id>[a-z0-9-]+)/$', views.report_list, name='report_list'),
    url(r'^report/detail/(?P<report_id>[a-z0-9]+)/$', views.report_detail, name='report_detail'),
    url(r'^video_show/(?P<lesson_id>[a-z|0-9]+)/$', views.video_show, name='video_show'),

    url(r'^monitor/lesson/(?P<lesson_id>[0-9]+)/$', views.lesson_monitor, name='lesson_monitor'),
    url(r'^schedule_list/$', views.schedule_list, name='schedule_list'),

    url(r'^statistics/(?P<course_id>[a-z0-9]+)/(?P<user_id>[a-z0-9-]+)/$', views.statistics_detail,
        name='statistics_detail'),
    url(r'^statistics/(?P<course_id>\d+)/$', views.statistics, name="statistics"),
    url(r'^exercises/lesson/(?P<lesson_id>\d+)/$', views.lesson_exercises, name='lesson_exercises'),
    url(r'^lesson/classroom/(?P<classroom_id>\d+)/management/$', views.lesson_classroom, name='lesson_classroom'),

    url(r'^class_statistics_list/$', views.class_statistics_list, name='class_statistics_list'),
    url(r'^class_statistics_detail/(?P<class_id>\d+)/$', views.class_statistics_detail, name='class_statistics_detail'),
    url(r'^user_statistics/(?P<user_id>\d+)/$', views.user_statistics, name='user_statistics'),
    url(r'^get_user_statistics/$', views.get_user_statistics, name='get_user_statistics'),
    url(r'^exam_statistics/$', views.exam_statistics, name='exam_statistics'),

    url(r'^show_report_detail/(?P<note_id>\d+)/$', views.show_report_detail, name='show_report_detail'),
]


from course.widgets import urls as widgets_urls

urlpatterns += [
    url(r'^widgets/', include(widgets_urls, namespace='widgets')),
]