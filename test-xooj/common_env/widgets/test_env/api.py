# -*- coding: utf-8 -*-
import json
import logging

from rest_framework import permissions, exceptions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from common_auth.models import User
from common_env.handlers import pool
from common_env.handlers.exceptions import MsgException, PoolFullException
from common_env.models import *

from .error import error
from .handlers import EnvHandler

logger = logging.getLogger(__name__)


def create_env(user_id, template_env_id, backend_admin):
    try:
        user = User.objects.get(pk=user_id)
        template_env = Env.objects.get(pk=template_env_id)
    except User.DoesNotExist as e:
        raise exceptions.NotFound(error.USER_NOT_EXIST)
    except Env.DoesNotExist as e:
        raise exceptions.NotFound(error.ENV_NOT_EXIST)

    executor = get_executor(user_id, template_env_id, backend_admin)
    env_handler = EnvHandler(user, backend_admin=backend_admin, executor=executor)
    try:
        env = env_handler.create(template_env)
    except MsgException as e:
        raise exceptions.PermissionDenied(e.message)
    except PoolFullException as e:
        raise exceptions.PermissionDenied(json.dumps(e.executor_info), code='PoolFull')
    except Exception as e:
        logger.error('create test env error[template_env=%s, user_id=%s]: %s' % (template_env_id, user.id, e))
        raise exceptions.APIException(error.CREATE_TEST_ENV_ERROR)
    return env


def get_executor(user_id, template_env_id, backend_admin):
    executor = {
        'func': create_env,
        'params': {
            'user_id': user_id,
            'template_env_id': template_env_id,
            'backend_admin': backend_admin,
        }
    }
    return executor


# 测试环境
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes((permissions.IsAuthenticated,))
def test_env(request):
    if request.method == 'GET':
        try:
            template_env_id = request.query_params['template_env']
            backend_admin = bool(request.query_params.get('from_backend'))
            is_complete = bool(request.query_params.get('is_complete'))
        except Exception as e:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        try:
            template_env = Env.objects.get(pk=template_env_id)
        except Env.DoesNotExist as e:
            raise exceptions.NotFound(error.ENV_NOT_EXIST)

        env_handler = EnvHandler(request.user, backend_admin=backend_admin)
        try:
            data = env_handler.get(template_env, is_complete=is_complete)
        except MsgException as e:
            raise exceptions.NotFound(e.message)

        return Response(data)

    elif request.method == 'POST':
        try:
            template_env_id = request.data['template_env']
            backend_admin = bool(request.data.get('from_backend'))
            _mode = request.data.get('_mode')
        except Exception as e:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        if _mode == 'remove_queue':
            executor = get_executor(request.user.id, template_env_id, backend_admin)
            pool.remove_executor(executor)
            return Response({})

        env = create_env(request.user.id, template_env_id, backend_admin)

        data = {
            'env_id': env.id
        }
        return Response(data)

    else:
        try:
            template_env_id = request.data['template_env']
            backend_admin = bool(request.data.get('from_backend'))
        except Exception as e:
            print e
            raise exceptions.ParseError(error.INVALID_PARAMS)

        try:
            template_env = Env.objects.get(pk=template_env_id)
        except Env.DoesNotExist as e:
            raise exceptions.NotFound(error.ENV_NOT_EXIST)

        env_handler = EnvHandler(request.user, backend_admin=backend_admin)
        try:
            env_handler.delete(template_env)
        except MsgException as e:
            raise exceptions.PermissionDenied(e.message)
        except Exception as e:
            logger.error('delete task env error[template_env=%s, user_id=%s]: %s' % (template_env_id, request.user.id, e))
            raise exceptions.APIException(error.DELETE_TEST_ENV_ERROR)

        return Response({})
