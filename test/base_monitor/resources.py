from django.db.models import Q

from base.utils.resource.config import Resource
from base_monitor.utils.common import get_script_path

from . import models


class MonitorCategory(Resource):
    model = models.MonitorCategory
    options = [{
        'check': {
            'get_conflict': lambda obj: models.MonitorCategory.objects.filter(
                Q(cn_name=obj.cn_name) | Q(en_name=obj.en_name),
            ).first(),
            'conflict_consistency_fields': ('cn_name', 'en_name'),
        },
    }]


def get_scripts_files(scripts):
    try:
        script_file_path = get_script_path(scripts.title, scripts.type)
    except Exception:
        return []
    else:
        return [script_file_path]


class Scripts(Resource):
    model = models.Scripts
    options = [{
        'to_one': {
            'category': {},
            'checker': {},
        },
        'force': {
            'create_user_id': 1,
            'last_edit_user_id': 1,
        },
        'check': {
            'conflict_consistency_fields': ('type', 'public', 'title', 'desc', 'code', 'suffix'),
        },
        'files': get_scripts_files,
    }]
