# -*- coding: utf-8 -*-
import json
import logging

from rest_framework import permissions, exceptions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from common_auth.models import User
from common_env.handlers import pool
from common_env.handlers.exceptions import MsgException, PoolFullException

from practice.api import get_task_object

from .error import error
from .handlers import EnvHandler
from .utils import get_remain_seconds, get_team


logger = logging.getLogger(__name__)



def create_env(user_id, team_id, task_hash, backend_admin):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist as e:
        raise exceptions.NotFound(error.USER_NOT_EXIST)

    team = get_team(team_id)
    task = get_task_object(task_hash)
    if not task:
        raise exceptions.NotFound(error.TASK_NOT_EXIST)

    executor = get_executor(user_id, team_id, task_hash, backend_admin)
    try:
        env_handler = EnvHandler(user, backend_admin=backend_admin, team=team, executor=executor)
    except MsgException as e:
        raise exceptions.NotFound(e.message)

    try:
        task_env = env_handler.create(task)
    except MsgException as e:
        raise exceptions.PermissionDenied(e.message)
    except PoolFullException as e:
        raise exceptions.PermissionDenied(json.dumps(e.executor_info), code='PoolFull')
    except Exception as e:
        logger.error('create taskenv error[task_hash=%s, user_id=%s]: %s' % (task_hash, user.id, e))
        raise exceptions.APIException(error.CREATE_TASK_ENV_ERROR)

    return task_env


def get_executor(user_id, team_id, task_hash, backend_admin):
    executor = {
        'func': create_env,
        'params': {
            'user_id': user_id,
            'team_id': team_id,
            'task_hash': task_hash,
            'backend_admin': backend_admin,
        }
    }
    return executor


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes((permissions.IsAuthenticated,))
def task_env(request):
    if request.method == 'GET':
        try:
            team_id = request.query_params.get('team')
            team_id = int(team_id) if team_id else None
            task_hash = request.query_params['task_hash']
            backend_admin = bool(request.query_params.get('from_backend'))
            is_complete = bool(request.query_params.get('is_complete'))
        except Exception as e:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        team = get_team(team_id)
        task = get_task_object(task_hash)
        if not task:
            raise exceptions.NotFound(error.TASK_NOT_EXIST)

        try:
            env_handler = EnvHandler(request.user, backend_admin=backend_admin, team=team)
        except MsgException as e:
            raise exceptions.NotFound(e.message)

        try:
            data = env_handler.get(task, is_complete=is_complete)
        except MsgException as e:
            raise exceptions.NotFound(e.message)

        return Response(data)

    elif request.method == 'POST':
        try:
            team_id = request.data.get('team')
            team_id = int(team_id) if team_id else None
            task_hash = request.data['task_hash']
            backend_admin = bool(request.data.get('from_backend'))
            _mode = request.data.get('_mode')
        except Exception as e:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        if _mode == 'remove_queue':
            executor = get_executor(request.user.id, team_id, task_hash, backend_admin)
            pool.remove_executor(executor)
            return Response({})

        task_env = create_env(request.user.id, team_id, task_hash, backend_admin)

        data = {
            'task_env_id': task_env.id,
            'env_id': task_env.env.id
        }
        return Response(data)

    else:
        try:
            team_id = request.data.get('team')
            team_id = int(team_id) if team_id else None
            task_hash = request.data['task_hash']
            backend_admin = bool(request.data.get('from_backend'))
        except Exception as e:
            print e
            raise exceptions.ParseError(error.INVALID_PARAMS)

        team = get_team(team_id)
        task = get_task_object(task_hash)
        if not task:
            raise exceptions.NotFound(error.TASK_NOT_EXIST)

        try:
            env_handler = EnvHandler(request.user, backend_admin=backend_admin, team=team)
        except MsgException as e:
            raise exceptions.NotFound(e.message)

        try:
            env_handler.delete(task)
        except MsgException as e:
            raise exceptions.PermissionDenied(e.message)
        except Exception as e:
            logger.error('delete taskenv error[task_hash=%s, user_id=%s]: %s' % (task_hash, request.user.id, e))
            raise exceptions.APIException(error.DELETE_TASK_ENV_ERROR)

        return Response({})


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def recover_task_env(request):
    try:
        task_hash = request.data['task_hash']
    except Exception as e:
        raise exceptions.ParseError(error.INVALID_PARAMS)

    task = get_task_object(task_hash)
    if not task:
        raise exceptions.NotFound(error.TASK_NOT_EXIST)

    try:
        env_handler = EnvHandler(request.user)
    except MsgException as e:
        raise exceptions.NotFound(e.message)

    try:
        env = env_handler.recover(task)
    except MsgException as e:
        raise exceptions.PermissionDenied(e.message)
    except Exception as e:
        raise exceptions.APIException(error.DELAY_TASKENV_ERROR)

    data = {
        'destroy_time': env.destroy_time,
        'remain_seconds': get_remain_seconds(env.destroy_time),
    }
    return Response(data)


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def delay_task_env(request):
    try:
        task_hash = request.data['task_hash']
    except Exception as e:
        raise exceptions.ParseError(error.INVALID_PARAMS)

    task = get_task_object(task_hash)
    if not task:
        raise exceptions.NotFound(error.TASK_NOT_EXIST)

    try:
        env_handler = EnvHandler(request.user)
    except MsgException as e:
        raise exceptions.NotFound(e.message)

    try:
        env = env_handler.delay(task)
    except MsgException as e:
        raise exceptions.PermissionDenied(e.message)
    except Exception as e:
        raise exceptions.APIException(error.DELAY_TASKENV_ERROR)

    data = {
        'destroy_time': env.destroy_time,
        'remain_seconds': get_remain_seconds(env.destroy_time),
    }
    return Response(data)


