from rest_framework import serializers
from common_cloud import models as cloud_models


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = cloud_models.Department
        fields = '__all__'


class UpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = cloud_models.UpdateInfo
        fields = '__all__'


class LicenseConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = cloud_models.LicenseConfig
        fields = '__all__'
