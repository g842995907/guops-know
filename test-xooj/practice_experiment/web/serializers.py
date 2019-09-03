# -*- coding: utf-8 -*-
from rest_framework import serializers

from practice_experiment.models import Direction


class DirectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direction
        fields = ('cn_name', 'en_name')
