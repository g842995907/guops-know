# -*- coding: utf-8 -*-
import json
import logging

from rest_framework import permissions, exceptions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from common_auth.models import User
from common_env.handlers import pool
from common_env.handlers.exceptions import MsgException, PoolFullException

from course.models import Lesson
from .error import error
from .handlers import EnvHandler
from .utils import get_remain_seconds, get_team


logger = logging.getLogger(__name__)



def create_env(user_id, team_id, lesson_hash, backend_admin):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist as e:
        raise exceptions.NotFound(error.USER_NOT_EXIST)

    team = get_team(team_id)
    try:
        lesson = Lesson.objects.get(pk=lesson_hash)
    except Lesson.DoesNotExist as e:
        raise exceptions.NotFound(error.LESSON_NOT_EXIST)

    executor = get_executor(user_id, team_id, lesson_hash, backend_admin)
    try:
        env_handler = EnvHandler(user, backend_admin=backend_admin, team=team, executor=executor)
    except MsgException as e:
        raise exceptions.NotFound(e.message)

    try:
        lesson_env = env_handler.create(lesson)
    except MsgException as e:
        raise exceptions.PermissionDenied(e.message)
    except PoolFullException as e:
        raise exceptions.PermissionDenied(json.dumps(e.executor_info), code='PoolFull')
    except Exception as e:
        logger.error('create lessonenv error[lesson_hash=%s, user_id=%s]: %s' % (lesson_hash, user.id, e))
        raise exceptions.APIException(error.CREATE_LESSON_ENV_ERROR)

    return lesson_env


def get_executor(user_id, team_id, lesson_hash, backend_admin):
    executor = {
        'func': create_env,
        'params': {
            'user_id': user_id,
            'team_id': team_id,
            'lesson_hash': lesson_hash,
            'backend_admin': backend_admin,
        }
    }
    return executor


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes((permissions.IsAuthenticated,))
def lesson_env(request):
    if request.method == 'GET':
        try:
            team_id = request.query_params.get('team')
            team_id = int(team_id) if team_id else None
            lesson_hash = request.query_params['lesson_hash']
            backend_admin = bool(request.query_params.get('from_backend'))
            is_complete = bool(request.query_params.get('is_complete'))
        except Exception as e:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        team = get_team(team_id)
        try:
            lesson = Lesson.objects.get(pk=lesson_hash)
        except Lesson.DoesNotExist as e:
            raise exceptions.NotFound(error.LESSON_NOT_EXIST)

        try:
            env_handler = EnvHandler(request.user, backend_admin=backend_admin, team=team)
        except MsgException as e:
            raise exceptions.NotFound(e.message)

        try:
            data = env_handler.get(lesson, is_complete=is_complete)
        except MsgException as e:
            raise exceptions.NotFound(e.message)

        return Response(data)

    elif request.method == 'POST':
        try:
            team_id = request.data.get('team')
            team_id = int(team_id) if team_id else None
            lesson_hash = request.data['lesson_hash']
            backend_admin = bool(request.data.get('from_backend'))
            _mode = request.data.get('_mode')
        except Exception as e:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        if _mode == 'remove_queue':
            executor = get_executor(request.user.id, team_id, lesson_hash, backend_admin)
            pool.remove_executor(executor)
            return Response({})

        lesson_env = create_env(request.user.id, team_id, lesson_hash, backend_admin)

        data = {
            'lesson_env_id': lesson_env.id,
            'env_id': lesson_env.env.id
        }
        return Response(data)

    else:
        try:
            team_id = request.data.get('team')
            team_id = int(team_id) if team_id else None
            lesson_hash = request.data['lesson_hash']
            backend_admin = bool(request.data.get('from_backend'))
        except Exception as e:
            print e
            raise exceptions.ParseError(error.INVALID_PARAMS)

        team = get_team(team_id)
        try:
            lesson = Lesson.objects.get(pk=lesson_hash)
        except Lesson.DoesNotExist as e:
            raise exceptions.NotFound(error.LESSON_NOT_EXIST)

        try:
            env_handler = EnvHandler(request.user, backend_admin=backend_admin, team=team)
        except MsgException as e:
            raise exceptions.NotFound(e.message)

        try:
            env_handler.delete(lesson)
        except MsgException as e:
            raise exceptions.PermissionDenied(e.message)
        except Exception as e:
            logger.error('delete lessonenv error[lesson_hash=%s, user_id=%s]: %s' % (lesson_hash, request.user.id, e))
            raise exceptions.APIException(error.DELETE_LESSON_ENV_ERROR)

        return Response({})


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def recover_lesson_env(request):
    try:
        lesson_hash = request.data['lesson_hash']
    except Exception as e:
        raise exceptions.ParseError(error.INVALID_PARAMS)

    try:
        lesson = Lesson.objects.get(pk=lesson_hash)
    except Lesson.DoesNotExist as e:
        raise exceptions.NotFound(error.LESSON_NOT_EXIST)

    try:
        env_handler = EnvHandler(request.user)
    except MsgException as e:
        raise exceptions.NotFound(e.message)

    try:
        env = env_handler.recover(lesson)
    except MsgException as e:
        raise exceptions.PermissionDenied(e.message)
    except Exception as e:
        raise exceptions.APIException(error.DELAY_LESSONENV_ERROR)

    data = {
        'destroy_time': env.destroy_time,
        'remain_seconds': get_remain_seconds(env.destroy_time),
    }
    return Response(data)


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def deplay_lesson_env(request):
    try:
        lesson_hash = request.data['lesson_hash']
    except Exception as e:
        raise exceptions.ParseError(error.INVALID_PARAMS)

    try:
        lesson = Lesson.objects.get(pk=lesson_hash)
    except Lesson.DoesNotExist as e:
        raise exceptions.NotFound(error.LESSON_NOT_EXIST)

    try:
        env_handler = EnvHandler(request.user)
    except MsgException as e:
        raise exceptions.NotFound(e.message)

    try:
        env = env_handler.delay(lesson)
    except MsgException as e:
        raise exceptions.PermissionDenied(e.message)
    except Exception as e:
        raise exceptions.APIException(error.DELAY_LESSONENV_ERROR)

    data = {
        'destroy_time': env.destroy_time,
        'remain_seconds': get_remain_seconds(env.destroy_time),
    }
    return Response(data)


