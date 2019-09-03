# -*- coding: utf-8 -*-
from rest_framework import serializers

from common_auth import models as auth_models


class FacultySerializer(serializers.ModelSerializer):
    class Meta:
        model = auth_models.Faculty
        fields = '__all__'


class MajorSerializer(serializers.ModelSerializer):
    class Meta:
        model = auth_models.Major
        fields = '__all__'


class ClassesSerializer(serializers.ModelSerializer):
    class Meta:
        model = auth_models.Classes
        fields = '__all__'
