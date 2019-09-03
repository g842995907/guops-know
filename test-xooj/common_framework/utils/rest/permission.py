from rest_framework import permissions


class IsStaffPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        if user.is_staff:
            return True

        return False

