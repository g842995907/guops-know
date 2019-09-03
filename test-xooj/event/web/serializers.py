# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from event import models as event_models
from event.cms import serializers as base_serializers
from event.utils import constants
from event.utils.task import TaskHandler


class EventSerializer(base_serializers.EventSerializer):
    logo = serializers.SerializerMethodField()

    def get_logo(self, obj):
        if obj.logo:
            return obj.logo.url
        else:
            return constants.DEDAULT_EVENT_LOGO_TEMPLATE(event_models.Event.Type.reverse_source[obj.type].lower())

    class Meta:
        model = event_models.Event
        fields = ('id', 'name', 'description', 'status',
                  'logo', 'start_time', 'end_time', 'public_rank', 'can_submit_writeup',
                  'type', 'mode', 'integral_mode', 'reward_mode', 'process')
        read_only_fields = ('name', 'description', 'status',
                  'logo', 'start_time', 'end_time', 'public_rank', 'can_submit_writeup',
                  'type', 'mode', 'integral_mode', 'reward_mode')


class EventSignupUserSerializer(base_serializers.EventSignupUserSerializer):
    token = serializers.SerializerMethodField()

    def get_token(self, obj):
        if obj.event.public_token:
            return obj.token
        else:
            return None

    class Meta:
        model = event_models.EventSignupUser
        fields = ('id', 'repr_name', 'repr_logo', 'event_name', 'event', 'token', 'status', 'time')
        read_only_fields = ('status', 'time', 'token')


class EventSignupTeamSerializer(base_serializers.EventSignupTeamSerializer):
    token = serializers.SerializerMethodField()

    def get_token(self, obj):
        if obj.event.public_token:
            return obj.token
        else:
            return None

    class Meta:
        model = event_models.EventSignupTeam
        fields = ('id', 'repr_name', 'repr_logo', 'team', 'event_name', 'event', 'token', 'status', 'time')
        read_only_fields = ('status', 'time', 'token', 'team')


class EventTaskSerializer(base_serializers.EventTaskSerializer):
    def get_task(self, obj):
        return TaskHandler.get_task_info(obj.task_hash)

    class Meta:
        model = event_models.EventTask
        fields = ('id', 'event', 'seq', 'task_hash', 'task_score', 'type', 'task', 'dynamic_score')
        read_only_fields = ('event', 'seq', 'task_hash', 'task_score', 'type')


class EventWriteupSerializer(base_serializers.EventWriteupSerializer):
    class Meta:
        model = event_models.EventWriteup
        fields = ('id', 'event', 'writeup', 'user', 'team', 'time')
        read_only_fields = ('user', 'team', 'time')


class EventUserSubmitLogSerializer(base_serializers.EventUserSubmitLogSerializer):
    class Meta:
        model = event_models.EventUserSubmitLog
        fields = ('id', 'event_task', 'answer', 'is_solved')


class EventUserAnswerSerializer(base_serializers.EventUserAnswerSerializer):
    task = serializers.SerializerMethodField()

    def get_task(self, obj):
        return TaskHandler.get_task_info(obj.event_task.task_hash)

    class Meta:
        model = event_models.EventUserAnswer
        fields = ('id', 'user', 'team', 'event_task', 'score', 'time', 'status', 'username', 'team_name', 'task')
        read_only_fields = ('user', 'team', 'event_task', 'answer', 'score', 'time', 'status')


class EventNoticeSerializer(base_serializers.EventNoticeSerializer):
    class Meta:
        model = event_models.EventNotice
        fields = ('id', 'event', 'notice', 'is_topped', 'create_time')
        read_only_fields = ('event', 'notice', 'is_topped', 'create_time')


class EventTaskNoticeSerializer(base_serializers.EventTaskNoticeSerializer):
    class Meta:
        model = event_models.EventTaskNotice
        fields = ('id', 'event_task', 'notice', 'is_topped', 'create_time')
        read_only_fields = ('event_task', 'notice', 'is_topped', 'create_time')


class EventTaskAccessLogSerializer(base_serializers.EventTaskAccessLogSerializer):
    pass