# -*- coding: utf-8 -*-

from django.utils import timezone
from rest_framework import exceptions

from common_auth.models import Team

from .error import error


def get_remain_seconds(destroy_time):
    if destroy_time:
        remain_seconds = (destroy_time - timezone.now()).total_seconds()
    else:
        remain_seconds = 0

    return remain_seconds


def get_team(team_id):
    if team_id:
        try:
            team = Team.objects.get(pk=team_id)
        except Team.DoesNotExist as e:
            raise exceptions.NotFound(error.TEAM_NOT_EXIST)
    else:
        team = None
    return team