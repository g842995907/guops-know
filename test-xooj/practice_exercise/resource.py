# -*- coding: utf-8 -*-

from common_env.models import Env
from practice import resource


class PracticeExerciseTaskMeta(resource.SolvedBaseTask):
    subsidiary = [{
        'force': {
            'create_user_id': None,
            'last_edit_user_id': None,
        },
        'subsidiary': {
            'category': {
                'get': lambda self: self.category,
                'set': lambda self, category: setattr(self, 'category', category),
            },
            'envs': {
                'many_to_many': True,
                'get': lambda self: self.envs.filter(env__status=Env.Status.TEMPLATE),
                'set': lambda self, task_envs: self.envs.add(*task_envs),
            },
        },
        'markdownfields': ['content', 'official_writeup']
    }]