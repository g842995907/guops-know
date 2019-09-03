from django.db.models import Q

from base.utils.resource.config import Resource

from base_traffic.utils.traffic import get_intelligent_traffic_script
from . import models


class TrafficCategory(Resource):
    model = models.TrafficCategory
    options = [{
        'check': {
            'get_conflict': lambda obj: models.TrafficCategory.objects.filter(
                Q(cn_name=obj.cn_name) | Q(en_name=obj.en_name),
            ).first(),
            'conflict_consistency_fields': ('cn_name', 'en_name'),
        },
    }]


class Traffic(Resource):
    model = models.Traffic
    options = [{
        'to_one': {
            'category': {},
            'parent': {
                'get': lambda obj: models.Traffic.objects.filter(id=obj.parent).first(),
                'set': lambda obj, parent: setattr(obj, 'parent', parent.id if parent else None),
            },
            'background_traffic': {
                'get': lambda obj: models.BackgroundTraffic.objects.filter(traffic=obj),
                'set': None,
                'rely_on': False,
            },
            'intelligent_traffic': {
                'get': lambda obj: models.IntelligentTraffic.objects.filter(traffic=obj),
                'set': None,
                'rely_on': False,
            },
        },
        'force': {
            'create_user_id': 1,
            'last_edit_user_id': 1,
        },
        'check': {
            'conflict_consistency_fields': ('type', 'title', 'introduction', 'public', 'is_copy', 'hash', 'parent'),
        },
    }]


class BackgroundTraffic(Resource):
    model = models.BackgroundTraffic
    options = [{
        'to_one': {
            'traffic': {},
            'trm': {},
        },
        'check': {
            'get_conflict': lambda obj: models.BackgroundTraffic.objects.filter(
                traffic__resource_id=obj.traffic.resource_id
            ).first(),
            'conflict_consistency_fields': ('pcap_file', 'file_name', 'file_name', 'file_name',
                                            'loop', 'mbps', 'multiplier', 'trm'),
        },
    }]


def get_intelligent_traffic_files(intelligent_traffic):
    return [get_intelligent_traffic_script(intelligent_traffic)]


class IntelligentTraffic(Resource):
    model = models.IntelligentTraffic
    options = [{
        'to_one': {
            'traffic': {},
            'tgm': {},
        },
        'check': {
            'get_conflict': lambda obj: models.IntelligentTraffic.objects.filter(
                traffic__resource_id=obj.traffic.resource_id
            ).first(),
            'conflict_consistency_fields': ('code', 'file_name', 'suffix', 'tgm'),
        },
        'files': get_intelligent_traffic_files,
    }]
