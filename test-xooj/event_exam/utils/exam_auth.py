from django.http import Http404

from event.utils import common as event_common
from django.shortcuts import render
from rest_framework.response import Response
import functools


def exam_auth_class(func):

    @functools.wraps(func)
    def get_auth(*args, **kwargs):
        try:
            user = args[0].user
        except:
            return render(args[0], 'web/404.html', context={})

        try:
            pk = kwargs.get("pk")
            exam = event_common.get_event_by_id(pk)
        except:
            return render(args[0], 'web/404.html', context={})

        if exam is None:
            return render(args[0], 'web/404.html', context={})

        if user.is_superuser:
            return func(*args, **kwargs)

        user_faculty = getattr(user, "faculty")
        user_major = getattr(user, "major")
        user_classes = getattr(user, "classes")

        auth_classes = exam.auth_classes.first()
        auth_major = exam.auth_major.first()
        auth_faculty = exam.auth_faculty.first()

        def privilege_match(auth, user_per):
            if auth == user_per:
                return func(*args, **kwargs)
            else:
                return render(args[0], 'web/404.html', context={})

        if auth_faculty:
            return privilege_match(auth_faculty, user_faculty)

        if auth_classes:
            return privilege_match(auth_classes, user_classes)

        if auth_major:
            return privilege_match(auth_major, user_major)

        return func(*args, **kwargs)

    return get_auth


def api_auth_permission(func):
    @functools.wraps(func)
    def get_auth(*args, **kwargs):
        try:
            user = args[1].user
        except:
            return Response({'response': {} , 'error_code': 1})

        try:
            pk = kwargs.get("pk")
            exam = event_common.get_event_by_id(pk)
        except:
            return Response({'response': {} , 'error_code': 1})

        if exam is None:
            return Response({'response': {} , 'error_code': 1})

        if user.is_superuser:
            return func(*args, **kwargs)

        user_faculty = getattr(user, "faculty")
        user_major = getattr(user, "major")
        user_classes = getattr(user, "classes")

        auth_classes = exam.auth_classes.first()
        auth_major = exam.auth_major.first()
        auth_faculty = exam.auth_faculty.first()

        def privilege_match(auth, user_per):
            if auth == user_per:
                return func(*args, **kwargs)
            else:
                return Response({'response': {} , 'error_code': 1})

        if auth_faculty:
            return privilege_match(auth_faculty, user_faculty)

        if auth_classes:
            return privilege_match(auth_classes, user_classes)

        if auth_major:
            return privilege_match(auth_major, user_major)

        return func(*args, **kwargs)

    return get_auth

