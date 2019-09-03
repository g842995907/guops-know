from base.utils.resource.config import Resource

from . import models


class TrafficEvent(Resource):
    model = models.TrafficEvent
    options = [{
        'to_one': {
            'traffic': {},
        },
        'force': {
            'pid': '',
            'error': None,
            'create_user_id': 1,
            'last_edit_user_id': 1,
        },
        'check': {
            'conflict_consistency_fields': ('title', 'introduction', 'type', 'start_up_mode', 'delay_time',
                                            'public', 'traffic', 'target', 'runner', 'target_net', 'parameter'),
        },
    }]
