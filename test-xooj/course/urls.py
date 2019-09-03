from django.conf.urls import url, include

from common_framework.utils.rest.routers import get_default_router
from course.web import viewset, views

viewsets = (
    viewset.DirectionViewSet,
    viewset.CourseViewSet,
    viewset.LessonViewSet,
    viewset.LessonNewViewSet,
    viewset.LessonScheduleViewSet,
    viewset.LessonJstreeViewSet,
    viewset.CourseScheduleViewSet,
)

router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),

    url(r'^list/$', views.list, name='list'),
    url(r'^theory_list/$', views.theory_list, name='theory_list'),
    url(r'^experiment_list/$', views.experiment_list, name='experiment_list'),
    url(r'^detail/(?P<course_id>[^/.]+)/$', views.detail_new, name='detail'),
    url(r'^detail_new/(?P<course_id>[^/.]+)/$', views.detail_new, name='detail_new'),
    url(r'^learn/(?P<course_id>[^/.]+)/$', views.learn, name='learn'),
    url(r'^learn/(?P<course_id>[^/.]+)/(?P<lesson_id>[^/.]+)/$', views.learn, name='learn_lesson'),
    url(r'^task/$', views.task, name='task'),
    url(r'^pdf/$', views.pdf, name='pdf'),
    url(r'^video/$', views.video, name='video'),
    url(r'^attachment/$', views.attachment, name='attachment'),
    url(r'^env/$', views.env, name='env'),
    url(r'^note/$', views.note, name='note'),
    url(r'^report/$', views.report, name='report'),
    url(r'^markdown/$', views.markdown, name='markdown'),
    url(r'^recommand/$', views.CourseRecommandView.as_view(), name='recommand'),

    # ===============================
    url(r'^learn_new/(?P<course_id>[^/.]+)/$', views.learn_new, name='learn_new'),
    url(r'^learn_new/(?P<course_id>[^/.]+)/(?P<lesson_id>[^/.]+)/$', views.learn_new, name='learn_new_lesson'),
    url(r'^markdown_new/$', views.markdown_new, name='markdown_new'),
    url(r'^pdf_new/$', views.pdf_new, name='pdf_new'),
    url(r'^video_new/$', views.video_new, name='video_new'),
    url(r'^attachment_new/$', views.attachment_new, name='attachment_new'),
    url(r'^env_new/$', views.env_new, name='env_new'),
    url(r'^note_new/$', views.note_new, name='note_new'),
    url(r'^report_new/$', views.report_new, name='report_new'),
    url(r'^env_load/$', views.env_load, name='env_load'),
    url(r'^network/(?P<course_id>\d+)/(?P<lesson_id>\d+)/$', views.network, name='network'),

    url(r"^exam_paper_detail/(?P<course_id>\d+)/(?P<lesson_id>\d+)/$", views.exam_paper_detail,
        name="exam_paper_detail"),

    url(r'^html/$', views.html, name='html'),
    url(r'^html/from_html_video/(?P<lesson_id>\d+)/$', views.from_html_video, name='from_html_video'),

    url(r'^lesson/(?P<lesson_id>[^/.]+)/attend_class_time/$', views.attend_class_time, name='attend_class_time'),

]
