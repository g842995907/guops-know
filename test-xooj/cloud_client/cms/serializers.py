from rest_framework import serializers
from cloud_client import models as cloud_models

class UpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = cloud_models.UpdateInfo
        fields = '__all__'
