from django.conf.urls import url, include

from common_framework.utils.rest.routers import get_default_router

from practice_experiment.cms import viewset, views

viewsets = (
    viewset.DirectionViewSet,
    viewset.ExperimentViewSet,
)

router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),

    url(r'^direction/$', views.direction, name='direction'),
    url(r'^direction/(?P<direction_id>[a-z|0-9]+)/$',
        views.direction_detail, name='direction_detail'),

    url(r'^experiments/$', views.experiments, name='experiments'),
    url(r'^experiment/(?P<experiments_id>[a-z0-9-]+)/$',
        views.experiment_detail, name='experiment_detail'),
    url(r'^experiment/custom_detail/(?P<experiment_id>[a-z|0-9]+)/$',
        views.custom_experiment_detail, name='custom_experiment_detail'),

    url(r'^auth_class/(?P<course_id>[a-z0-9]+)/$',
        views.auth_class, name='auth_class'),
    url(r'^practice_categories/(?P<type_id>[a-z0-9]+)/$',
        views.practice_categories, name='practice_categories'),
]
