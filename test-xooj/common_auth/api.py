# -*- coding: utf-8 -*-
from django.db.models import Q

from common_auth import models as auth_model
from common_auth.constant import GroupType
from common_framework.models import AuthAndShare


def get_all_class(faculty=None, major=None):
    all_class = auth_model.Classes.objects.all()
    if major:
        all_class = all_class.filter(major=major)
    elif faculty:
        all_class = all_class.filter(faculty=faculty)

    return all_class


def get_all_teachers():
    teachers = auth_model.User.objects.exclude(status=auth_model.User.USER.DELETE).filter(
        groups__id=GroupType.TEACHER)

    return teachers


def get_faculty():
    return auth_model.Faculty.objects.all()


def get_major(faculty=None):
    major = auth_model.Major.objects.all()
    if faculty:
        major = major.filter(faculty=faculty)

    return major


def oj_auth_class(func):
    def get_auth(view_set):
        queryset = view_set.queryset
        user = view_set.request.user

        if user.is_superuser:
            return func(view_set)

        user_faculty = getattr(user, "faculty")
        user_major = getattr(user, "major")
        user_classes = getattr(user, "classes")
        create_user_filed = getattr(view_set, 'create_user_filed') if \
            hasattr(view_set, 'create_user_filed') else None
        if not create_user_filed:
            create_user_filed = 'create_user'
        view_set.queryset = (queryset.filter(
            Q(auth_faculty__in=[user_faculty], auth=AuthAndShare.AuthMode.CUSTOM_AUTH_MODE)) | queryset.filter(
            Q(auth_major__in=[user_major], auth=AuthAndShare.AuthMode.CUSTOM_AUTH_MODE)) | queryset.filter(
            Q(auth_classes__in=[user_classes], auth=AuthAndShare.AuthMode.CUSTOM_AUTH_MODE) |
            Q(auth=AuthAndShare.AuthMode.ALL_AUTH_MODE) |
            Q(**{'{create_user_filed}'.format(create_user_filed=create_user_filed): user})
        )).distinct()
        # if user_classes:
        #     if not isinstance(user_classes, list):
        #         user_classes = [user_classes]
        #     view_set.queryset = queryset.filter(Q(auth_classes__in=user_classes))
        #     #view_set.queryset = queryset.filter(Q(auth_classes__in=user_classes) | Q(auth_classes__isnull=True))
        # else:
        #     view_set.queryset = queryset.filter(auth_classes__isnull=True)
        return func(view_set)

    return get_auth


def oj_share_teacher(func):
    def get_share(view_set):
        queryset = view_set.queryset
        user = view_set.request.user

        create_user_filed = getattr(view_set, 'create_user_filed') if \
            hasattr(view_set, 'create_user_filed') else None
        if not create_user_filed:
            create_user_filed = 'create_user'

        if user.is_superuser:
            return func(view_set)

        if not isinstance(user, list):
            share_teacher = [user]

        view_set.queryset = queryset.filter(
            Q(share_teachers__in=share_teacher, share=AuthAndShare.ShareMode.CUSTOM_SHARE_MODE) |
            Q(**{'{create_user_filed}'.format(create_user_filed=create_user_filed): user}) |
            Q(share=AuthAndShare.ShareMode.ALL_SHARE_MODE)
        ).distinct()

        return func(view_set)

    return get_share


def task_share_teacher(func):
    def get_share(view_set):
        if not hasattr(view_set, 'is_ignore_share') or (
                    hasattr(view_set, 'is_ignore_share') and not view_set.is_ignore_share()):
            queryset = view_set.queryset
            user = view_set.request.user

            create_user_filed = getattr(view_set, 'create_user_filed') if \
                hasattr(view_set, 'create_user_filed') else None
            if not create_user_filed:
                create_user_filed = 'create_user'

            if user.is_superuser:
                return func(view_set)

            if not isinstance(user, list):
                share_teacher = [user]

            view_set.queryset = queryset.filter(
                Q(event__share_teachers__in=share_teacher, event__share=AuthAndShare.ShareMode.CUSTOM_SHARE_MODE) |
                Q(**{'event__{create_user_filed}'.format(create_user_filed=create_user_filed): user}) |
                Q(event__share=AuthAndShare.ShareMode.ALL_SHARE_MODE)
            ).distinct()
        return func(view_set)

    return get_share
