# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.hashers import make_password
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from rest_framework import serializers, exceptions
from rest_framework.validators import UniqueValidator

from common_auth.constant import TeamUserStatus, TeamStatus
from common_auth.models import User, Faculty, Major, Classes, Team, TeamUser, TeamUserNotice
from event.models import EventSignupTeam
from x_person.web import error
from x_person.setting import api_settings


class UserSerializer(serializers.ModelSerializer):
    faculty_name = serializers.SerializerMethodField()
    major_name = serializers.SerializerMethodField()
    classes_name = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'faculty_name', 'major_name', 'classes_name', 'team_name', 'logo_url', 'id', 'username',
            'email', 'faculty', 'major', 'classes', 'logo', 'team', 'first_name', 'email', 'nickname', 'mobile',
            'address', 'ID_number', 'brief_introduction', 'student_id','status')

    def get_faculty_name(self, obj):
        if obj.faculty:
            return obj.faculty.name
        else:
            return None

    def get_major_name(self, obj):
        if obj.major:
            return obj.major.name
        else:
            return None

    def get_classes_name(self, obj):
        if obj.classes:
            return obj.classes.name
        else:
            return None

    def get_team_name(self, obj):
        if obj.team:
            return obj.team.name
        else:
            return None

    def get_logo_url(self, obj):
        if obj.logo:
            return obj.logo.url
        else:
            return None

    def to_internal_value(self, data):
        new_password = data.get('new_pwd', None)
        reset_password = data.get('reset_password', None)
        logo = data.get('logo', None)
        if logo and logo.name.split('.')[-1] not in api_settings.LOGO_WHITE_LIST:
            raise exceptions.NotAcceptable(_('x_only_pic_file'))

        ret = super(UserSerializer, self).to_internal_value(data)
        if new_password:
            password = make_password(new_password)
            ret['password'] = password
        if reset_password:
            password = make_password(reset_password)
            ret['password'] = password
        return ret


class TeamSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    team_leader_name = serializers.SerializerMethodField()
    join_contest_number = serializers.SerializerMethodField()
    team_member_number = serializers.SerializerMethodField()
    apply_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ('logo_url', 'team_leader_name', 'name', 'create_time', 'brief_introduction', 'join_contest_number',
                  'team_member_number', 'apply_count', 'id', 'logo')
        extra_kwargs = {
            'name': {'validators': [
                UniqueValidator(queryset=Team.objects.filter(status__in=[TeamStatus.NORMAL, TeamStatus.FORBID]))]}
        }

    def get_logo_url(self, obj):
        if obj.logo:
            return obj.logo.url
        else:
            return None

    def validate_create_time(self, value):
        if value > timezone.now():
            raise exceptions.ValidationError(error.NOW_TIME_ERROE)
        return value

    def get_team_leader_name(self, obj):
        team_leader = TeamUser.objects.filter(team_id=obj.id, team_leader=True, status=TeamUserStatus.JOIN)
        if team_leader:
            return team_leader.first().user.username
        else:
            return None

    def get_join_contest_number(self, obj):
        return EventSignupTeam.objects.filter(team_id=obj.id).count()

    def get_team_member_number(self, obj):
        return TeamUser.objects.filter(team_id=obj.id, status=TeamUserStatus.JOIN).count()

    def get_apply_count(self, obj):
        return TeamUser.objects.filter(team_id=obj.id, status=TeamUserStatus.NEED_JOIN, has_handle=False).count()

    # def update(self, instance, validated_data):
    #     instance.create_time = validated_data.get('create_time', instance.create_time)
    #     instance.brief_introduction = validated_data.get('brief_introduction', instance.brief_introduction)
    #     instance.save()
    #     return instance


class TeamUserSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    real_name = serializers.SerializerMethodField()
    user_logo_url = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()

    class Meta:
        model = TeamUser
        fields = (
            'id', 'username', 'status', 'has_handle', 'modify_time', 'team_leader', 'create_time', 'user_logo_url',
            'user', 'real_name', 'team_name')

    def get_username(self, obj):
        return obj.user.username

    def get_user_logo_url(self, obj):
        if obj.user.logo:
            return obj.user.logo.url
        else:
            return None

    def get_real_name(self, obj):
        return obj.user.first_name

    def get_team_name(self, obj):
        return obj.team.name



class TeamUserNoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamUserNotice
        fields = ('user', 'has_notice', 'content', 'id')


class FacultySerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = '__all__'


class MajorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Major
        fields = '__all__'


class ClassesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classes
        # fields = '__all__'
        fields = ('id', 'name', 'major', 'major_name', 'faculty', 'faculty_name')
