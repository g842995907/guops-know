from base.utils.resource.config import Resource

from base_monitor.models import Scripts
from base_mission import constant
from base_mission.utils.mission_data_handle import get_related_mission_script_path
from . import models


class Mission(Resource):
    model = models.Mission
    options = [{
        'to_one': {
            'ctf_mission': {
                'get': lambda obj: models.CTFMission.objects.filter(mission=obj),
                'set': None,
                'rely_on': False,
            },
            'check_mission': {
                'get': lambda obj: models.CheckMission.objects.filter(mission=obj),
                'set': None,
                'rely_on': False,
            },
        },
        'to_many': {
            'exam_tasks': {
                'get': lambda obj: models.ExamTask.objects.filter(exam=obj),
                'set': None,
            }
        },
        'force': {
            'mission_status': constant.MissionStatus.COMMING,
            'create_user_id': 1,
            'last_edit_user_id': 1,
        },
        'check': {
            'conflict_consistency_fields': ('type', 'title', 'content', 'score', 'public', 'difficulty', 'period'),
        },
    }]


class CTFMission(Resource):
    model = models.CTFMission
    options = [{
        'to_one': {
            'mission': {},
        },
        'check': {
            'get_conflict': lambda obj: models.CTFMission.objects.filter(
                mission__resource_id=obj.mission.resource_id
            ).first(),
            'conflict_consistency_fields': ('target', 'flag'),
        },
    }]


def get_check_mission_files(check_mission):
    script_path = get_related_mission_script_path(check_mission)
    return [script_path]


class CheckMission(Resource):
    model = models.CheckMission
    options = [{
        'to_one': {
            'mission': {},
            'script': {
                'get': lambda obj: Scripts.objects.filter(id=obj.script_id).first(),
                'set': lambda obj, scripts: setattr(obj, 'script_id', scripts.id if scripts else 0),
            },
        },
        'check': {
            'get_conflict': lambda obj: models.CheckMission.objects.filter(
                mission__resource_id=obj.mission.resource_id
            ).first(),
            'conflict_consistency_fields': ('check_type', 'checker_id', 'target_net', 'target', 'scripts',
                                            'is_once', 'first_check_time', 'is_polling', 'interval', 'params',
                                            'status_description'),
        },
        'files': get_check_mission_files,
    }]


class ExamTask(Resource):
    model = models.ExamTask
    options = [{
        'to_one': {
            'exam': {},
        },
        'check': {
            'get_conflict': lambda obj: models.ExamTask.objects.filter(
                exam__resource_id=obj.exam.resource_id,
                task_title=obj.task_title,
            ).first(),
            'conflict_consistency_fields': ('task_title', 'task_content', 'task_type', 'option', 'answer',
                                            'task_index', 'task_score'),
        },
    }]
