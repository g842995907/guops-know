from django.db.models import Q
from django.utils import timezone
from common_auth.utils import is_admin
from common_framework.utils.cache import CacheProduct, delete_cache

from event import models as event_models

DEFAULT_CACHE_TIME = 60 * 60 * 2
def get_user_event(user, pk):
    if is_admin(user):
        event = event_models.Event.objects.get(pk=pk)
    else:
        event = event_models.Event.objects.filter(Q(create_user=user) | Q(share_teachers=user)).distinct().get(pk=pk)
    return event


def get_user_event_queryset(user, queryset):
    if not is_admin(user):
        return queryset.filter(Q(create_user=user) | Q(share_teachers=user)).distinct()
    return queryset


def get_user_event_related_queryset(user, queryset):
    if not is_admin(user):
        return queryset.filter(Q(event__create_user=user) | Q(event__share_teachers=user)).distinct()
    return queryset


def get_user_event_task_related_queryset(user, queryset):
    if not is_admin(user):
        return queryset.filter(Q(event_task__event__create_user=user) | Q(event_task__event__share_teachers=user)).distinct()
    return queryset


def get_process(obj):
    if hasattr(obj, 'process'):
        return obj.process
    else:
        now = timezone.now()
        if obj.start_time <= now < obj.end_time:
            return event_models.Event.Process.INPROGRESS
        elif obj.start_time > now:
            return event_models.Event.Process.COMING
        elif obj.end_time < now:
            return event_models.Event.Process.OVER
    return None


def is_team_mode(event):
    if not event:
        return False

    if event.mode == event_models.Event.Mode.TEAM:
        return True
    return False


def get_event_by_id(id):
    event_cache = CacheProduct('event')
    key = 'get_event_id_%s' % id
    event = event_cache.get(key, None)
    if event:
        return event

    try:
        event = event_models.Event.objects.get(id=id)
    except event_models.Event.DoesNotExist as e:
        return None

    if event:
        event_cache.set(key, event, DEFAULT_CACHE_TIME)

    return event


def delete_event_cache(id):
    event_cache = CacheProduct('event')
    key = 'get_event_id_%s' % id
    event_cache.set(key, None, DEFAULT_CACHE_TIME)