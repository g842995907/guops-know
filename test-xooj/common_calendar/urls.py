from django.conf.urls import url, include

from common_calendar.api import CalendarViewSet
from common_framework.utils.rest.routers import get_default_router

viewsets = (
   CalendarViewSet,
)

router = get_default_router(viewsets)
urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),
]