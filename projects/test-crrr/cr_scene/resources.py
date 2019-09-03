from base.utils.resource.config import Resource

from . import models


class CrScene(Resource):
    model = models.CrScene
    options = [{
        'to_one': {
            'scene_config': {},
        },
        'to_many': {
            'missions': {},
            'traffic_events': {},
            'mission_periods': {
                'get': lambda obj: models.MissionPeriod.objects.filter(cr_scene=obj),
                'set': None,
            },
        },
        'force': {
            'scene_id': None,
        },
        'check': {
            'conflict_consistency_fields': ('name', 'roles'),
        },
    }]


class MissionPeriod(Resource):
    model = models.MissionPeriod
    options = [{
        'to_one': {
            'cr_scene': {},
        },
        'check': {
            'get_conflict': lambda obj: models.MissionPeriod.objects.filter(
                cr_scene__resource_id=obj.cr_scene.resource_id,
                period_name=obj.period_name
            ).first(),
            'conflict_consistency_fields': ('period_index',),
        },
    }]
