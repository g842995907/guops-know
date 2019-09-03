# -*- coding: utf-8 -*-
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.utils.translation import ugettext_lazy as _

from base.utils.rest.serializers import ModelSerializer
from base_traffic.cms.serializers import BackgroundDataSerializer, IntelligentDataSerializer, BaseRepNameSerializer
from traffic_event.models import TrafficEvent


class BaseCategorySerializer(ModelSerializer):
    category = serializers.SerializerMethodField()

    def get_category(self, obj):
        return obj.traffic.category.id if obj.traffic.category else None


class TrafficEventSerializer(BaseRepNameSerializer, ModelSerializer):
    title = serializers.CharField(validators=[UniqueValidator(queryset=TrafficEvent.objects.all(),
                                                              message=_('x_name_unique'))])

    class Meta:
        model = TrafficEvent
        fields = "__all__"


class BackgroundTrafficEventSerializer(BaseCategorySerializer, BaseRepNameSerializer, ModelSerializer):
    traffic = BackgroundDataSerializer()

    class Meta:
        model = TrafficEvent
        fields = "__all__"


class IntelligentTrafficEventSerializer(BaseCategorySerializer, BaseRepNameSerializer, ModelSerializer):
    traffic = IntelligentDataSerializer()

    class Meta:
        model = TrafficEvent
        fields = "__all__"
