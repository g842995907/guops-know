# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from event import models as event_models
from event.web import serializers as base_serializers
from rest_framework import serializers
from django.utils import timezone


class EventSerializer(base_serializers.EventSerializer):
    remain_seconds = serializers.SerializerMethodField()
    server_time = serializers.SerializerMethodField()

    def get_remain_seconds(self, obj):
        if obj.process == event_models.Event.Process.INPROGRESS:
            return (timezone.now() - obj.start_time).total_seconds()
        elif obj.process == event_models.Event.Process.COMING:
            return (obj.end_time - timezone.now()).total_seconds()
        else:
            return None

    def get_server_time(self, obj):
        return serializers.DateTimeField().to_representation(timezone.now())

    class Meta:
        model = event_models.Event
        fields = ('id', 'name', 'description', 'rule',
                  'logo', 'start_time', 'end_time', 'process', 'hash', 'remain_seconds', 'server_time')
        read_only_fields = ('name', 'description', 'rule',
                            'logo', 'start_time', 'end_time', 'hash')


class EventSignupUserSerializer(base_serializers.EventSignupUserSerializer):
    pass


class EventSignupTeamSerializer(base_serializers.EventSignupTeamSerializer):
    pass


class EventTaskSerializer(base_serializers.EventTaskSerializer):
    pass


class EventWriteupSerializer(base_serializers.EventWriteupSerializer):
    pass


class EventUserSubmitLogSerializer(base_serializers.EventUserSubmitLogSerializer):
    pass


class EventUserAnswerSerializer(base_serializers.EventUserAnswerSerializer):
    pass


class EventNoticeSerializer(base_serializers.EventNoticeSerializer):
    pass


class EventTaskNoticeSerializer(base_serializers.EventTaskNoticeSerializer):
    pass
