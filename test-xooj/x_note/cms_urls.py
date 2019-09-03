from django.conf.urls import url, include

from common_framework.utils.rest.routers import get_default_router

from x_note import cms_views
from x_note.cms import viewset


viewsets = (
    viewset.NoteViewSet,
)

router = get_default_router(viewsets)

urlpatterns = [
    url(r'^notes/$', cms_views.note_list, name='note_list'),
    url(r'^detail/(?P<note_id>[a-z0-9-]+)/$', cms_views.note_detail, name='note_detail'),
    url(r'^getRecordLoadsStatus/$', cms_views.getRecordLoadsStatus, name='record_loads_status'),
]

urlpatterns += [
    url(r'^api/', include(router.urls, namespace='api')),
]
