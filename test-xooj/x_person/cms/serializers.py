# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
from datetime import timedelta

from django.contrib.auth.models import Group, Permission
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, exceptions
from rest_framework.validators import UniqueValidator

from common_auth.constant import TeamStatus
from common_auth.models import User, Faculty, Major, Classes, Team, TeamUser
from common_auth.setting import api_settings as auth_api_settings
from common_framework.utils.image import save_image
from x_person.response import REGEX


class UserSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField()
    faculty_name = serializers.SerializerMethodField()
    major_name = serializers.SerializerMethodField()
    classes_name = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()
    online = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'faculty_name', 'major_name', 'classes_name', 'team_name', 'logo_url', 'id', 'username', 'password',
            'email', 'faculty', 'major', 'classes', 'logo', 'team', 'first_name', 'email', 'group_name', 'groups',
            'nickname', 'mobile', 'address', 'ID_number', 'brief_introduction', 'is_active', 'student_id', 'is_staff',
            'status', "expired_time", 'last_login', 'last_login_ip', 'online', 'total_online_time', 'is_superuser')
        extra_kwargs = {'password': {'write_only': True}}

    def get_group_name(self, obj):
        if obj.is_superuser:
            return Group.objects.get(id=1).name
        if obj.groups.first():
            return obj.groups.first().name
        else:
            return _('x_student')

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

    def get_online(self, obj):
        if obj.report_time:
            critical_time = timezone.now() - timedelta(seconds=auth_api_settings.OFFLINE_TIME)
            if obj.report_time >= critical_time:
                return User.Online.ONLINE
            else:
                return User.Online.OFFLINE
        else:
            return User.Online.OFFLINE

    def to_internal_value(self, data):
        full_logo_name = data.get('logo', None)
        password = data.get('password', None)
        data._mutable = True
        if full_logo_name:
            logofile = save_image(full_logo_name)
            data['logo'] = logofile
        data._mutable = False
        ret = super(UserSerializer, self).to_internal_value(data)
        if password:
            pattern_password = re.compile(unicode(REGEX.REGEX_PASSWORD))
            if not pattern_password.match(password):
                from x_person.web.response import ResError
                raise exceptions.NotAcceptable(ResError.NEW_PASSWORD_WRONG)
            password = make_password(password)
            ret['password'] = password
        return ret


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


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name', 'permissions')


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('id', 'name', 'content_type', 'codename')


class TeamSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    team_leader_name = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ('logo_url', 'team_leader_name', 'create_time', 'name', 'status', 'id', 'logo', 'brief_introduction')
        extra_kwargs = {
            'name': {'validators': [UniqueValidator(queryset=Team.objects.filter(status__in=[TeamStatus.NORMAL, TeamStatus.FORBID]))]}
        }

    def get_logo_url(self, obj):
        if obj.logo:
            return obj.logo.url
        else:
            return None

    def get_team_leader_name(self, obj):
        team_leader = TeamUser.objects.filter(team_id=obj.id, team_leader=True)
        if team_leader:
            return team_leader.first().user.first_name
        else:
            return None

    def to_internal_value(self, data):
        full_logo_name = data.get('logo', None)
        data._mutable = True
        if full_logo_name:
            logofile = save_image(full_logo_name)
            data['logo'] = logofile
        data._mutable = False
        ret = super(TeamSerializer, self).to_internal_value(data)
        return ret


class TeamUserSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    real_name = serializers.SerializerMethodField()

    class Meta:
        model = TeamUser
        fields = ('username', 'status', 'team_leader', 'real_name')

    def get_username(self, obj):
        return obj.user.username

    def get_real_name(self, obj):
        return obj.user.first_name


class TeamUserModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = TeamUser
        fields = "__all__"

