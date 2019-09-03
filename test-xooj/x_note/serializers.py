# -*- coding: utf-8 -*-
from rest_framework import serializers

from x_note.models import Note


class NoteSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()

    def get_user_name(self, obj):
        return obj.user.first_name

    def get_teacher_name(self, obj):
        if obj.teacher:
            return obj.teacher.first_name

    class Meta:
        model = Note
        fields = ('id', 'content', 'user', 'username', 'resource',
                  'resource_name', 'create_time',
                  'update_time', 'content_abstract', 'score', 'ispass', 'markcomment', 'teacher', 'teacher_name',
                  'user_name', 'public')
