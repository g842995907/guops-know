# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from common_framework.utils.image import save_image
from event_exam import models as event_models
from event.cms import serializers as base_serializers

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class EventSerializer(base_serializers.EventSerializer):
    class Meta:
        model = event_models.Event
        fields = (
            'id', 'name', 'description', 'rule', 'logo', 'start_time', 'end_time', 'status',
            'public', 'public_rank', 'public_all_rank', 'can_submit_writeup', 'process', 'status',
            'creater_username', 'is_other_share', 'auth', 'auth_count', 'all_auth_count', 'share', 'share_count'
        )

    def to_internal_value(self, data):
        full_logo_name = data.get('logo', None)
        data._mutable = True

        if full_logo_name:
            logofile = save_image(full_logo_name)
            data['logo'] = logofile
        data._mutable = False
        ret = super(EventSerializer, self).to_internal_value(data)
        return ret


class ExtendEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = event_models.extendEvent
        fields = ('event', 'ans_display_method', 'score_status', 'rank_status', 'capabili_name')


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


class EventRankSerializer(serializers.Serializer):
    obj_id = serializers.IntegerField()
    obj_name = serializers.CharField(max_length=2048)
    sum_score = serializers.IntegerField()
    submit_time = serializers.DateTimeField()


class ListEventRankSerializer(object):
    def __init__(self, row):
        self.data = {

            'obj_id': row.get('obj_id'),
            'obj_username': row.get('obj_username'),
            'obj_name': row.get('obj_name'),
            'sum_score': row.get('sum_score'),
            'writeup_score': row.get('writeup_score'),
            'submit_time': row.get('submit_time'),
            'status': row.get('status'),

        }
