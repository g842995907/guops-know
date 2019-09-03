from rest_framework import serializers

from x_comment.models import Comment
from x_comment.models import NewLikes


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'tenant', 'username', 'nickname', 'avatar',
                  'resource', 'comment', 'source_ip', 'thumbs_up',
                  'public', 'parent', 'create_time', 'update_time',
                  'comment_username', 'theme_name')


class CommentListViewSerializer:
    def __init__(self, log):
        self.data = {
            'id': log.get('id'),
            'title': log.get('title'),
            'comment': log.get('comment'),
            'last_update': log.get('last_update'),
            'resource_url': log.get('resource_url'),
        }


class CommentSerializerLike(serializers.ModelSerializer):
    class Meta:
        model = NewLikes
        fields = (
            'id', 'username', 'username_id', 'resource',
            'create_time', 'updata_time', 'status', 'comment'
        )
