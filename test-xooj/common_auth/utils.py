
from common_auth.constant import GroupType


ADMIN_GROUPS = (
    GroupType.ADMIN,
    GroupType.TEACHER,
)


def is_admin(user):
    if user.is_superuser:
        return True
    group = user.groups.first()
    return group.id in ADMIN_GROUPS if group else False