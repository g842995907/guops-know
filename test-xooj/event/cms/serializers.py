# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils import timezone
from django.utils.html import escape

from rest_framework import serializers

from event import models as event_models
from event.utils import constants
from event.utils.task import TaskHandler, EventTaskHandler

from common_framework.utils.rest import serializers as common_serializers


class EventSerializer(serializers.ModelSerializer,
                      common_serializers.BaseAuthAndShareSerializer,
                      common_serializers.CreateUserNameAndShareSerializer):
    process = serializers.SerializerMethodField()

    def get_process(self, obj):
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

    class Meta:
        model = event_models.Event
        fields = (
            'id', 'name', 'description', 'rule', 'logo', 'start_time', 'end_time', 'status',
            'public', 'public_rank', 'public_all_rank', 'public_token', 'can_submit_writeup',
            'type', 'mode', 'integral_mode', 'reward_mode', 'process',
            'auth', 'auth_count', 'share', 'share_count'
        )


class BaseEventSignupSerializer(serializers.ModelSerializer):
    event_name = serializers.SerializerMethodField()
    repr_name = serializers.SerializerMethodField()
    repr_logo = serializers.SerializerMethodField()

    def get_event_name(self, obj):
        return escape(obj.event.name)

    class Meta:
        model = event_models.BaseEventSignup


class EventSignupUserSerializer(BaseEventSignupSerializer):
    def get_repr_name(self, obj):
        return obj.user.first_name or obj.user.first_name

    def get_repr_logo(self, obj):
        return obj.user.logo.url if obj.user.logo else constants.DEDAULT_USER_LOGO

    class Meta:
        model = event_models.EventSignupUser
        fields = ('id', 'repr_name', 'repr_logo', 'user', 'event_name', 'token', 'status', 'time')
        read_only_fields = ('time',)


class EventSignupTeamSerializer(BaseEventSignupSerializer):
    def get_repr_name(self, obj):
        return obj.team.name

    def get_repr_logo(self, obj):
        return obj.team.logo.url if obj.team.logo else constants.DEDAULT_TEAM_LOGO

    class Meta:
        model = event_models.EventSignupTeam
        fields = ('id', 'repr_name', 'repr_logo', 'team', 'event_name', 'token', 'status', 'time')
        read_only_fields = ('time',)


class EventTaskSerializer(serializers.ModelSerializer):
    task = serializers.SerializerMethodField()
    dynamic_score = serializers.SerializerMethodField()

    def get_task(self, obj):
        return TaskHandler.get_task_info(obj.task_hash, backend=True)

    def get_dynamic_score(self, obj):
        if obj.event.integral_mode == event_models.Event.IntegralMode.DYNAMIC:
            return EventTaskHandler.get_task_current_dynamic_score(obj)[0]
        else:
            return 0

    class Meta:
        model = event_models.EventTask
        fields = ('id', 'event', 'seq', 'task_hash', 'task_score', 'public', 'type', 'task', 'dynamic_score')
        read_only_fields = ('type',)


class EventWriteupSerializer(serializers.ModelSerializer):
    class Meta:
        model = event_models.EventWriteup
        fields = ('id', 'event', 'writeup', 'user', 'team', 'time')
        read_only_fields = ('user', 'event', 'writeup', 'team', 'time')


class EventUserSubmitLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = event_models.EventUserSubmitLog
        fields = ('id', 'user', 'team', 'event_task', 'answer', 'score', 'is_solved', 'time', 'submit_ip')
        read_only_fields = ('user', 'team', 'event_task', 'answer', 'score', 'is_solved', 'time', 'submit_ip')


class EventUserAnswerSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.user.first_name or obj.user.username

    def get_team_name(self, obj):
        return obj.team.name if obj.team else ''

    class Meta:
        model = event_models.EventUserAnswer
        fields = ('id', 'user', 'team', 'event_task', 'answer', 'score', 'time', 'status', 'username', 'team_name')
        read_only_fields = ('user', 'team', 'event_task', 'answer', 'time')


class BaseNoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = event_models.BaseNotice


class EventNoticeSerializer(BaseNoticeSerializer):
    class Meta:
        model = event_models.EventNotice
        fields = ('id', 'event', 'notice', 'is_topped', 'create_time')
        read_only_fields = ('create_time',)


class EventTaskNoticeSerializer(BaseNoticeSerializer):
    class Meta:
        model = event_models.EventTaskNotice
        fields = ('id', 'event_task', 'notice', 'is_topped', 'create_time')
        read_only_fields = ('create_time',)


class EventSignupUserDetailSerializer(EventSignupUserSerializer):
    solved_count = serializers.IntegerField()
    sum_score = serializers.IntegerField()
    last_submit_time = serializers.DateTimeField()

    class Meta:
        model = event_models.EventSignupUser
        fields = (
            'id', 'repr_name', 'repr_logo', 'user', 'event_name', 'token', 'status', 'time', 'solved_count',
            'sum_score',
            'last_submit_time')
        read_only_fields = ('time',)


class EventSignupTeamDetailSerializer(EventSignupTeamSerializer):
    solved_count = serializers.IntegerField()
    sum_score = serializers.IntegerField()
    last_submit_time = serializers.DateTimeField()

    class Meta:
        model = event_models.EventSignupTeam
        fields = (
            'id', 'repr_name', 'repr_logo', 'team', 'event_name', 'token', 'status', 'time', 'solved_count',
            'sum_score',
            'last_submit_time')
        read_only_fields = ('time',)


class EventTaskAccessLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = event_models.EventTaskAccessLog
        fields = ('id', 'event_task', 'user', 'time')
        read_only_fields = ('user', 'time')
