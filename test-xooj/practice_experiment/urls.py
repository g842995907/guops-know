from django.conf.urls import url, include


from common_framework.utils.rest.routers import get_default_router
from practice_experiment.web import viewset, views

viewsets = (
    viewset.DirectionViewSet,
    viewset.ExperimentViewSet,
)

router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),

    url(r'^list/$', views.list, name='list'),
    url(r'^learn/(?P<experiment_id>[^/.]+)/$', views.learn, name='learn'),
    url(r'^task/$', views.task, name='task'),
    url(r'^video/$', views.video, name='video'),
    url(r'^note/$', views.note, name='note'),
]
