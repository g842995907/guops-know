# -*-i coding: utf-8 -*-

from rest_framework import serializers

from common_message.models import Message

class MessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Message
        exclude = ('id', )


class MessageManageSerializer(serializers.ModelSerializer):
    un_read_message_count = serializers.IntegerField()






