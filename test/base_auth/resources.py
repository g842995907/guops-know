
from base.utils.resource.config import Resource

from . import models


class Organization(Resource):
    model = models.Organization
    options = [{
        'to_one': {
            'parent': {},
        },
        'check': {
            'get_conflict': lambda obj: models.Organization.objects.filter(name=obj.name).first(),
            'conflict_consistency_fields': ('name',),
        },
    }]


class User(Resource):
    model = models.User
    options = [{
        'to_custom': {
            'groups': {
                'get': lambda obj: obj.group,
                'set': lambda obj, value: obj.groups.set([value]) if value else None,
            },
            'user_permissions': {
                'get': lambda obj: [p.pk for p in obj.user_permissions.all()],
                'set': lambda obj, value: obj.user_permissions.set(value),
            },
        },
        'check': {
            'conflict_consistency_fields': ('username', 'password', 'logo', 'nickname', 'name', 'profile',
                                            'organization'),
        },
    }]
