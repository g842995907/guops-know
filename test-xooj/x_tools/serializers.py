from rest_framework import serializers

from common_auth.models import User
from common_framework.utils.image import save_image

from x_tools.models import Tool, ToolCategory, ToolComment


class ToolCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolCategory
        fields = ('id', 'cn_name', 'en_name')


class ToolCommentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    tool = serializers.PrimaryKeyRelatedField(queryset=Tool.objects.all())
    username = serializers.SerializerMethodField()
    tool_name = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.user.username

    def get_tool_name(self, obj):
        return obj.tool.name

    class Meta:
        model = ToolComment
        fields = ('id', 'user', 'tool', 'comment', 'parent', 'thumbs_up',
                  'create_time', 'update_time', 'username', 'tool_name')


class ToolSerializer(serializers.ModelSerializer):
    category_i18n_names = serializers.SerializerMethodField()
    category_names = serializers.SerializerMethodField()
    creater_username = serializers.SerializerMethodField()
    knowledges_list = serializers.SerializerMethodField()

    def get_knowledges_list(self, obj):
        if obj.knowledges:
            return obj.knowledges.split(",")

    def get_creater_username(self, obj):
        if obj.create_user:
            return obj.create_user.first_name or obj.create_user.username
        else:
            return None

    def to_internal_value(self, data):
        full_logo_name = data.get('cover', None)
        category = data.get('category', None)
        platforms = data.get('platforms', None)
        language = data.get('language', None)
        online = data.get('online', None)

        data._mutable = True
        if category:
            data['category'] = ",".join(data.getlist('category'))
        if language:
            data['language'] = ",".join(data.getlist('language'))
        if platforms:
            data['platforms'] = ",".join(data.getlist('platforms'))
        # if online:
        #     data['platforms'] = "online"
        # else:
        #     data['online'] = False

        if full_logo_name:
            logofile = save_image(full_logo_name)
            data['cover'] = logofile
        # else:
        #     del data['cover']
        # if not data.get("save_path"):
        #     del data["save_path"]
        if not data.get("public"):
            data['public'] = False

        data._mutable = False
        return super(ToolSerializer, self).to_internal_value(data)

    def get_category_i18n_names(self, data):
        categories = []
        for cate_id in data.category.split(","):
            try:
                categories.append(ToolCategory.objects.get(id=cate_id))
            except Exception, e:
                pass
        try:
            language = self.context.get("request").LANGUAGE_CODE
            if language != "zh-hans":
                return ",".join([cate.en_name for cate in categories])
        except Exception, e:
            pass
        return ",".join([cate.cn_name for cate in categories])

    def get_category_names(self, obj):
        categories = []
        try:
            language = self.context.get('request').LANGUAGE_CODE
            for cate_id in obj.category.split(","):
                try:
                    categories.append(ToolCategory.objects.get(id=cate_id))
                except Exception, e:
                    pass
            if language == 'en':
                return ",".join([cate.en_name for cate in categories])
        except:
            pass
        return ",".join([cate.cn_name for cate in categories])

    class Meta:
        model = Tool
        fields = ('id', 'hash', 'name', 'category', 'save_path', 'cover', 'lock',
                  'size', 'version', 'homepage', 'platforms', 'category_i18n_names',
                  'language','license_model', 'introduction', 'category_names', 'builtin',
                  'category_ids', 'public', 'online', 'create_time', 'update_time', 'creater_username', 'knowledges', 'knowledges_list')
