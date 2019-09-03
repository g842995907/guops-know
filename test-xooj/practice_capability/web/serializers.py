# -*- coding: utf-8 -*-
from django.db.models.aggregates import Sum
from rest_framework import serializers

from practice_capability import models as capability_modules
from practice_capability.models import TestPaperRecord


class TestPaperSerializer(serializers.ModelSerializer):
    finish = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()

    def get_finish(self, obj):
        return TestPaperRecord.objects.filter(test_paper=obj, submit_user=self.context.get('request').user).exists()

    def get_score(self, obj):
        score_sum = TestPaperRecord.objects.filter(test_paper=obj,
                                                   submit_user=self.context.get('request').user).aggregate(Sum("score"))
        return score_sum.get('score__sum')

    class Meta:
        model = capability_modules.TestPaper
        fields = '__all__'


class TestPaperTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = capability_modules.TestPaperTask
        fields = '__all__'
