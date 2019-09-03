# -*-coding: utf-8 -*-
import hashlib

from django.conf import settings
from django.utils.datetime_safe import date, datetime

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from common_calendar.models import Calendar
from common_calendar.serializer import CalendarSerializer
from common_framework.utils import cache as cache_utils
from common_framework.utils.rest.mixins import CacheModelMixin

CALENDAR_COURSE = 0
CALENDAR_PARCTICE_REAl = 6
CALENDAR_PARCTICE_EXE = 1
CALENDAR_DOWNTOOL = 2
CALENDAR_COLLECT = 3
CALENDAR_EXAM = 4
CALENDAR_CONTEXT = 5


def add_calendar(title, content, type, url, is_event, user=None,
                 faculty=None, major=None, classes=None, team=None, show_time=None):
    if not show_time:
        show_time = date.today()

    key_calendar = "%s-%s-%d-%s-%s-%s-%s-%s-%s-%s" % \
                   (
                       title, content, type, str(url),
                       str(getattr(user, "username", "none")),
                       str(getattr(faculty, "name", "none")),
                       str(getattr(major, "name", "none")),
                       str(getattr(classes, "name", "none")),
                       str(getattr(team, "name", "none")),
                       str(show_time),
                   )
    key_calendar = hashlib.md5(key_calendar).hexdigest().decode("utf-8")
    obj = _calendar_cache_instance.get(key_calendar)
    if not obj:
        obj = Calendar.objects.filter(title=title, content=content, type=type, url=url, is_event=is_event, user=user,
                                      faculty=faculty, major=major, classes=classes, team=team, show_time=show_time)
    if obj:
        return

    obj = Calendar.objects.create(
        title=title,
        content=content,
        type=type,
        url=url,
        is_event=is_event,
        user=user,
        faculty=faculty,
        major=major,
        classes=classes,
        team=team,
    )

    cache_utils.delete_cache(_calendar_cache_instance)
    _calendar_cache_instance.set(key_calendar, obj, settings.DEFAULT_CACHE_AGE)


class CalendarViewSet(CacheModelMixin, ReadOnlyModelViewSet):
    serializer_class = CalendarSerializer
    permissions_class = (IsAuthenticated,)
    unlimit_pagination = True

    def get_queryset(self):
        user = self.request.user
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        day = self.request.GET.get('day')

        if not year or not month:
            today = date.today()
            year = today.year
            month = today.month
        if not day:
            queryset = Calendar.objects.filter(show_time__month=month, show_time__year=year)
        else:
            queryset = Calendar.objects.filter(show_time__day=day, show_time__month=month, show_time__year=year)
        queryset_ret = queryset.filter(user=user)

        if user.team:
            queryset_ret |= queryset.filter(team=user.team)

        if user.major:
            queryset_ret |= queryset.filter(major=user.major)

        if user.faculty:
            queryset_ret |= queryset.filter(faculty=user.faculty)

        if user.classes:
            queryset_ret |= queryset.filter(classes=user.classes)

        return queryset_ret


cache_name = "%s-%s" % (CalendarViewSet.__module__, CalendarViewSet.__name__)
_calendar_cache_instance = cache_utils.CacheProduct(cache_name)


def calendar_init():
    Calendar.objects.all().delete()
    cache_utils.delete_cache(_calendar_cache_instance)
