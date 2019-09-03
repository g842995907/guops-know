# -*- coding: utf-8 -*-

from practice import resource


class ChoiceTaskMeta(resource.BaseTaskMeta):
    check = [{
        'get_conflict_obj': lambda resource: resource.model.objects.filter(
            hash=resource.obj.hash,
        ).first(),
        'conflict_consistency_check': lambda obj, conflict_obj: \
            obj.content == conflict_obj.content
            and obj.event == conflict_obj.event
    }, {
        'root': 'practice.models.TaskEvent',
        'get_conflict_obj': lambda resource: resource.model.objects.filter(
            content=resource.obj.content,
            event=resource.obj.event,
            is_copy=False
        ).first(),
    }]
    subsidiary = [{
        'force': {
            'create_user_id': None,
            'last_edit_user_id': None,
        },
        'subsidiary': {
            'category': {
                'get': lambda self: self.category,
                'set': lambda self, category: setattr(self, 'category', category),
            }
        },
        'markdownfields': ['content', 'option']
    }]