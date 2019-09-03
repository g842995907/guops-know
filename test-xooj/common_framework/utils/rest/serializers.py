from rest_framework import serializers
from rest_framework.serializers import Serializer

from common_auth.models import User
from common_auth.utils import is_admin
from common_framework.utils.constant import Status
from common_framework.utils.request import is_en as is_en_request


def is_en(serializer):
    request = serializer.context.get('request', None)
    return is_en_request(request)


class BaseAuthSerializer(Serializer):
    auth_count = serializers.SerializerMethodField()
    all_auth_count = serializers.SerializerMethodField()

    def get_auth_count(self, obj):
        if obj.pk is None:
            return 0

        return len(obj.auth_classes.filter(status=Status.NORMAL))

    def get_all_auth_count(self, obj):
        if obj.pk is None:
            return 0

        return sum([
            len(obj.auth_faculty.filter(status=Status.NORMAL)),
            len(obj.auth_major.filter(status=Status.NORMAL)),
            len(obj.auth_classes.filter(status=Status.NORMAL))
        ])


class BaseShareSerializer(Serializer):
    share_count = serializers.SerializerMethodField()

    def get_share_count(self, obj):
        if obj.pk is None:
            return 0

        return len(obj.share_teachers.exclude(status=User.USER.DELETE))


class BaseAuthAndShareSerializer(
    BaseAuthSerializer,
    BaseShareSerializer):
    pass


class BaseCreateNameSerializer(Serializer):
    creater_username = serializers.SerializerMethodField()

    def get_creater_username(self, obj):
        if hasattr(obj, 'create_user') and obj.create_user:
            return obj.create_user.first_name or obj.create_user.username
        elif hasattr(obj, 'user') and obj.user:
            return obj.user.first_name or obj.user.username

        return None


class CreateUserNameAndShareSerializer(BaseCreateNameSerializer):
    is_other_share = serializers.SerializerMethodField()

    def get_is_other_share(self, obj):
        context = self.context
        if not context.get('request'):
            return False

        user = context['request'].user
        if is_admin(user):
            return False

        user_id = user.id

        if hasattr(obj, 'create_user') and obj.create_user:
            return True if user_id != obj.create_user.id else False
        elif hasattr(obj, 'user') and obj.user:
            return True if user_id != obj.user.id else False

        return False
