# -*- coding: utf-8 -*-
import json
from rest_framework import serializers

from base_mission import models as mission_models, constant
from base_mission.utils.handle_func import check_required_valid
from cr_scene.models import CrScene
from base_mission.constant import Type


class ExamTaskSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(max_length=20, required=True)
    task_type = serializers.IntegerField(min_value=0, max_value=3, required=True)

    default_error_messages = {
        'OPTION_REQUIRED': 'Options Required',
        'OPTION_TYPE': 'Options should be a list',
        'INVALID_OPTION': 'Invalid Option',
        'INVALID_ANSWER': 'Invalid Answer',
    }

    def validate(self, attrs):
        if attrs.get('task_type') != constant.TopicProblem.SHORTQUES:
            option = attrs.get('option')
            if not option:
                self.fail('OPTION_REQUIRED')

            options = json.loads(option)
            if type(options) != list:
                self.fail('OPTION_TYPE')

            for task_option in options:
                if task_option.keys() != ['optionLabel', 'optionValue']:
                    self.fail('INVALID_OPTION')

            ans_list = list(attrs.get('answer')) if (attrs.get('task_type') == constant.TopicProblem.MULTIPLE) else [
                attrs.get("answer")]
            label_list = [op.get('optionLabel') for op in options]
            for ans in ans_list:
                if ans not in label_list:
                    self.fail('INVALID_ANSWER')

        return attrs

    class Meta:
        model = mission_models.ExamTask
        fields = '__all__'


class MissionSerializer(serializers.ModelSerializer):
    create_user_name = serializers.CharField(source='create_user.username', default='')

    title = serializers.CharField(max_length=20)
    type = serializers.IntegerField(min_value=min(constant.Type.values()), max_value=max(constant.Type.values()))
    difficulty = serializers.IntegerField(min_value=min(constant.Difficulty.values()),
                                          max_value=max(constant.Difficulty.values()), required=False)
    extra_data = serializers.SerializerMethodField()
    period_name = serializers.SerializerMethodField()

    default_error_messages = {
        'EXIST_TITLE': 'Title Already Exists',
    }

    def get_period_name(self, obj):
        try:
            per = obj.crscene_set.first().missionperiod_set.filter(
                period_index=(obj.period - 1),
                status=constant.Status.NORMAL
            ).first()
            if per:
                return per.period_name
            else:
                return ''
        except Exception:
            return ''

    def create(self, validated_data):
        data = self.initial_data
        exist_missions = CrScene.objects.get(id=data.get('cr_scene_id')).missions.all()
        title = data.get('title')
        if exist_missions.filter(title=title).exists():
            self.fail('EXIST_TITLE')

        if validated_data['type'] == mission_models.Mission.Type.CHECK:
            # checker 默认发布
            validated_data['public'] = True
        return super(MissionSerializer, self).create(validated_data)

    def get_extra_data(self, obj):
        if obj.type == Type.EXAM:
            return ExamTaskSerializer(obj.examtask_set.filter(status=1), many=True).data
        elif obj.type == Type.CHECK:
            return CheckSerializer(getattr(obj, 'checkmission')).data
        elif obj.type == Type.CTF:
            return CTFSerializer(getattr(obj, 'ctfmission')).data
        return ''

    class Meta:
        model = mission_models.Mission
        fields = "__all__"


class CTFSerializer(serializers.ModelSerializer):
    class Meta:
        model = mission_models.CTFMission
        fields = '__all__'


class CheckSerializer(serializers.ModelSerializer):
    check_type = serializers.IntegerField(min_value=min(constant.CheckType.values()),
                                          max_value=max(constant.CheckType.values()))

    def validate(self, attrs):
        if attrs.get('check_type') == constant.CheckType.SYSTEM:
            required_fields = ['target_net', 'checker_id']
            check_required_valid(data=attrs, required_fields=required_fields)
        return attrs

    class Meta:
        model = mission_models.CheckMission
        fields = '__all__'


class CTFMissionSerializer(MissionSerializer):
    ctfmission = CTFSerializer()

    class Meta:
        model = mission_models.Mission
        fields = '__all__'


class CheckMissionSerializer(MissionSerializer):
    checkmission = CheckSerializer()

    class Meta:
        model = mission_models.Mission
        fields = '__all__'
