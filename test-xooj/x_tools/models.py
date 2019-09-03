from __future__ import unicode_literals
import uuid

from django.db import models
from django.utils.translation import ugettext as _

from common_auth.models import User
from common_framework.utils.constant import Status
from common_framework.models import ShowLock, Builtin
from x_tools.file_utils import ToolPath, ToolCoverPath


class ToolCategory(models.Model):
    cn_name = models.CharField(max_length=255)
    en_name = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'xtool_category'

    def __unicode__(self):
        return self.cn_name


def tool_hash():
    return "{}.tool".format(uuid.uuid4())


class Tool(ShowLock, Builtin):
    RUNS_ON = (
        ('windows', _("Windows")),
        ('linux', _("Linux")),
        ('mac', _("Mac OS")),
        ('android', _("Android")),
        ('ios', _("IOS")),
        ('others', _("Others"))
    )
    LICENESE_MODEL = (
        ('free', _("FREE")),
        ('trial', _("TRIAL")),
        ('non-free', _("Non-Free"))
    )
    name = models.CharField(max_length=255)
    hash = models.CharField(max_length=100, null=True, default=tool_hash)
    save_path = models.FileField(upload_to=ToolPath('tools'), null=True, blank=True)
    cover = models.ImageField(upload_to=ToolCoverPath('tool_covers'), null=True, blank=True)
    size = models.CharField(max_length=64, null=True, blank=True)
    version = models.CharField(max_length=64, null=True, blank=True)
    homepage = models.URLField(null=True, blank=True)
    online = models.BooleanField(default=False)
    # category = models.ManyToManyField(ToolCategory, related_name="category")
    category = models.CharField(max_length=255)
    platforms = models.CharField(max_length=255)
    language = models.CharField(max_length=255)
    license_model = models.CharField(max_length=64, choices=LICENESE_MODEL)
    introduction = models.TextField(null=True, blank=True)
    knowledges = models.CharField(max_length=1024, null=True)
    public = models.BooleanField(default=True)
    status = models.PositiveIntegerField(default=Status.NORMAL)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    create_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='tool_create_user', null=True, default=None)

    class Meta:
        db_table = 'xtool_tool'

    def __unicode__(self):
        return self.name

    def category_names(self):
        categories = []
        for cate_id in self.category.split(","):
            try:
                categories.append(ToolCategory.objects.get(id=cate_id))
            except Exception, e:
                pass
        return ",".join([cate.cn_name for cate in categories])

    def category_ids(self):
        ids = self.category.split(",")
        return [int(id) for id in ids if id]


class AbstractComment(models.Model):
    parent = models.ForeignKey('self', blank=True, null=True, default=None, related_name='child')

    class Meta:
        abstract = True


class ToolComment(AbstractComment):
    user = models.ForeignKey(User, related_name="user_id")
    tool = models.ForeignKey(Tool, related_name="tool_id")
    comment = models.TextField()
    thumbs_up = models.IntegerField(default=0)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'xtool_comment'
        ordering = ["-create_time"]

    def __unicode__(self):
        return self.comment
