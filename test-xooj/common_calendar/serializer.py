# -*-i coding: utf-8 -*-

from rest_framework import serializers

from common_calendar.models import Calendar


class CalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calendar
        exclude = ('id', 'team', 'user',
                   'faculty', 'major', 'classes', )
