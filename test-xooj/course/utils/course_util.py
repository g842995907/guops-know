# -*- coding: utf-8 -*-
import copy
import json
import math
import os
import logging

from django.db.models import F
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions

from common_framework.utils.scan import scan_file
from common_framework.utils.enum import enum
from common_framework.utils.unique import generate_unique_key

from common_auth.models import User
from common_auth.constant import GroupType
from common_resource.execute import Dumper, Loader
from common_resource.setting import api_settings as resource_api_settings
from common_env.handlers.exceptions import MsgException, PoolFullException
from common_env.handlers.manager import Getter, admin_delete_env
from common_env.handlers.pool import get_executor_info
from common_env.models import Env
from ..models import LessonEnv, ClassroomGroupInfo, CourseUserStat
from ..constant import CourseResError
from ..widgets.env.handlers import EnvHandler
from event.utils.task import TaskHandler as BaseTaskHandler


logger = logging.getLogger(__name__)

Method_Type = enum(
    COURSE_CREATE=0,
    LESSON_CREATE=1,
    LESSON_DELETE=2,
    PUBLIC=3,
    LESSON_UPDATE=4,
)


def dump_course(queryset):
    dumper = Dumper(queryset)
    if queryset.count() > 1:
        filename = 'course_{}.zip'.format(timezone.now().strftime('%Y%m%d%H%M%S'))
    else:
        course_name = queryset[0].name
        filename = 'course_{}.zip'.format(course_name)
    file_path = dumper.dumps(filename)
    return file_path


def scan_course_resource():
    return scan_file(resource_api_settings.LOAD_TMP_DIR, r'^course_.+?.zip$')


def load_course(filename):
    path = os.path.join(resource_api_settings.LOAD_TMP_DIR, filename)
    loader = Loader()
    loader.loads(path)


def lesson_jstree_CURD(method_type, modelclass, instance, **kwargs):
    if method_type == Method_Type.COURSE_CREATE:
        # 增加课时jstree根目录
        flag = False
        jstree_course_obj = modelclass.objects.filter(
            self_id__startswith="course_",
            course_id=instance.id,
            lesson=None,
        ).first()
        if not jstree_course_obj:
            jstree_course_obj = modelclass.objects.create(
                self_id="course_" + str(instance.id),
                course_id=instance.id,
                lesson=None,
                # text=instance.name,
            )
            flag = True
        jstree_course_obj.text = instance.name
        jstree_course_obj.save()

        return jstree_course_obj, flag

    elif method_type == Method_Type.LESSON_CREATE or method_type == Method_Type.LESSON_UPDATE:
        # 增加课时jstree子目录
        course_instance = get_class_instance(modelclass, instance)
        modelclass_instance = modelclass.objects.filter(lesson=instance).first()
        if modelclass_instance:
            modelclass_instance.course_id = instance.course.id
            modelclass_instance.text = instance.name
            modelclass_instance.public = instance.public
            modelclass_instance.save()
        else:
            modelclass.objects.create(
                self_id="lesson_" + str(instance.id),
                course_id=instance.course.id,
                lesson_id=instance.id,
                parent=course_instance.self_id,
                text=instance.name,
                type=modelclass.Type.FILE,
                public=instance.public
            )
    elif method_type == Method_Type.LESSON_DELETE:
        # 删除课时jstree子目录
        ids = kwargs.pop("ids", False)
        if ids is not False:
            modelclass.objects.filter(lesson_id__in=ids).delete()
            return True
        modelclass.objects.filter(lesson_id=instance.id).delete()
    elif method_type == Method_Type.PUBLIC:
        queryset = kwargs.pop("queryset", False)
        public = kwargs.pop("public", False)

        if queryset is not False and public is not False:
            ids = queryset.values_list("id", flat=True)
            modelclass_queryset = modelclass.objects.filter(lesson_id__in=ids)
            modelclass_ids = modelclass_queryset.values_list('lesson_id', flat=True)
            modelclass_queryset.update(public=public)

            # 处理原始数据出现隐藏被删除，重新进行创建
            data_list = []
            course_instance = get_class_instance(modelclass, queryset[0])
            queryset = queryset.exclude(id__in=list(modelclass_ids))
            for instance in queryset:
                tempdata = modelclass(
                    self_id="lesson_" + str(instance.id),
                    course_id=instance.course.id,
                    lesson_id=instance.id,
                    parent=course_instance.self_id,
                    text=instance.name,
                    type=modelclass.Type.FILE,
                    public=instance.public,
                )
                data_list.append(tempdata)
            modelclass.objects.bulk_create(data_list)
    return True


def get_class_instance(modelclass, lesson_instance):
    try:
        course_instance = modelclass.objects.get(course_id=lesson_instance.course.id, parent='#')
    except Exception as e:
        logger.info('that we can\'t find this information from this model {}'.format(modelclass))
        raise exceptions.NotFound(CourseResError.NOT_FOUND_JSTREE)
    return course_instance


def _new_group(user_ids):
    group = {
        'users': user_ids,
    }
    return group


def check_class_groups(classes, groups):
    user_ids = []
    for group in groups:
        user_ids.extend(group['users'])
    real_user_ids = [user.id for user in classes.user_set.exclude(status=User.USER.DELETE).filter(groups=GroupType.USER)]
    if (set(user_ids) - set(real_user_ids)) or (set(real_user_ids) - set(user_ids)):
        return False

    return True


def get_class_group_info(classes, groups):
    users = classes.user_set.exclude(status=User.USER.DELETE).filter(groups=GroupType.USER)
    user_dict = {user.id: user for user in users}

    group_infos = []
    for group in groups:
        group_info = {}
        group_user_ids = group['users']
        user_list = []
        for user_id in group_user_ids:
            user = user_dict.pop(user_id, None)
            if user:
                user_list.append({
                    'id': user.id,
                    'name': user.first_name or user.username,
                })
        group_info['users'] = user_list
        group_infos.append(group_info)

    if user_dict:
        group_changed = True
        group_user_len = sum([len(group['users']) for group in groups])
        avg_len = int(math.ceil(group_user_len * 1.0 / len(groups))) if groups else 0
        extra_user_ids = user_dict.keys()
        index = 0
        while extra_user_ids[index: index + avg_len]:
            group_user_ids = extra_user_ids[index: index + avg_len]
            group = _new_group(group_user_ids)
            groups.append(group)

            user_list = []
            for user_id in group_user_ids:
                user = user_dict.pop(user_id, None)
                if user:
                    user_list.append({
                        'id': user.id,
                        'name': user.first_name or user.username,
                    })
            group_infos.append({
                'users': user_list
            })
            index = index + avg_len
    else:
        group_changed = False

    return {
        'group_changed': group_changed,
        'groups': groups,
        'group_infos': group_infos,
    }


def get_class_group_env_info(class_group):
    classes = class_group.classroom.classes
    groups = json.loads(class_group.groups)
    info_ret = get_class_group_info(classes, groups)
    groups = info_ret['groups']
    group_infos = info_ret['group_infos']
    group_changed = info_ret['group_changed']
    group_lesson_envs = class_group.classroom.lesson.envs.filter(type=LessonEnv.Type.GROUP)

    lesson_env_ids = []
    group_keys = []
    for i, group_info in enumerate(group_infos):
        group = groups[i]
        if 'key' not in group:
            group_changed = True
        group_key = group.setdefault('key', generate_unique_key())
        group_keys.append(group_key)
        lesson_env_id = group.get('lesson_env')
        if lesson_env_id:
            lesson_env_ids.append(lesson_env_id)

        group_info['key'] = group_key

    lesson_env_map = {lesson_env.id: lesson_env for lesson_env in group_lesson_envs.filter(pk__in=lesson_env_ids)}
    group_wait_map = {wait.extra: wait for wait in class_group.waits.filter(extra__in=group_keys)}
    for i, group_info in enumerate(group_infos):
        group = groups[i]
        wait = group_wait_map.get(group_info['key'])
        if wait:
            group_info['wait'] = get_executor_info(instance=wait)

        lesson_env_id = group.get('lesson_env')
        if lesson_env_id:
            group_lesson_env = lesson_env_map.get(lesson_env_id)
            if group_lesson_env:
                estimate_consume_time = Getter.get_estimate_env_consume_time(group_lesson_env.env.json_config)
                loaded_seconds, remain_seconds = Getter.get_estimate_remain_seconds(group_lesson_env.env.create_time,
                                                                                    estimate_consume_time)
                group_info['env'] = {
                    'status': group_lesson_env.env.status,
                    'error': group_lesson_env.env.error,
                    'loaded_seconds': loaded_seconds,
                    'estimate_consume_time': estimate_consume_time,
                }

    if group_changed:
        class_group.groups = json.dumps(groups)
        class_group.save()

    return group_infos


def create_default_class_group_info(classroom):
    users = classroom.classes.user_set.exclude(status=User.USER.DELETE).filter(groups=GroupType.USER)
    groups = [_new_group([user.id]) for user in users]
    return ClassroomGroupInfo.objects.create(
        classroom=classroom,
        groups=json.dumps(groups),
    )


def update_class_group_info(classroom_group_info, groups):
    from ..widgets.env.error import error
    old_groups = json.loads(classroom_group_info.groups)
    for group in old_groups:
        lesson_env_id = group.get('lesson_env')
        if lesson_env_id:
            using_status = Env.ActiveStatusList
            lesson_env = LessonEnv.objects.filter(pk=lesson_env_id).first()
            if lesson_env and lesson_env.env and lesson_env.env.status in using_status:
                raise exceptions.PermissionDenied(error.NO_PERMISSION)

    if not check_class_groups(classroom_group_info.classroom.classes, groups):
        raise exceptions.PermissionDenied(error.NO_PERMISSION)

    for group in groups:
        group['key'] = generate_unique_key()
        group['lesson_env'] = None
    classroom_group_info.groups = json.dumps(groups)
    classroom_group_info.save()
    return classroom_group_info


def create_group_env(user_id, class_group_id, group_key):
    from ..widgets.env.error import error

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist as e:
        raise exceptions.PermissionDenied(error.NO_PERMISSION)

    try:
        class_room_group_info = ClassroomGroupInfo.objects.get(pk=class_group_id)
    except Exception as e:
        raise exceptions.PermissionDenied(error.NO_PERMISSION)

    groups = json.loads(class_room_group_info.groups)
    group_dict = {group['key']: group for group in groups}
    if group_key not in group_dict:
        raise exceptions.PermissionDenied(error.NO_PERMISSION)

    group = group_dict[group_key]
    lesson_env_id = group.get('lesson_env')
    if lesson_env_id:
        using_status = Env.ActiveStatusList
        lesson_env = LessonEnv.objects.filter(pk=lesson_env_id).first()
        if lesson_env and lesson_env.env and lesson_env.env.status in using_status:
            raise exceptions.PermissionDenied(error.NO_PERMISSION)

    lesson = class_room_group_info.classroom.lesson
    executor = get_create_group_env_executor(user_id, class_group_id, group_key)
    try:
        env_handler = EnvHandler(user, executor=executor)
    except MsgException as e:
        raise exceptions.NotFound(e.message)

    try:
        lesson_env = env_handler.create(lesson, group_users=group['users'])
    except MsgException as e:
        raise exceptions.PermissionDenied(e.message)
    except PoolFullException as e:
        class_room_group_info.waits.add(e.executor_instance)
        raise e
    except Exception as e:
        logger.error('create lessonenv error[lesson_hash=%s, user_id=%s]: %s' % (lesson.id, user.id, e))
        raise exceptions.APIException(error.CREATE_LESSON_ENV_ERROR)

    group['lesson_env'] = lesson_env.id
    class_room_group_info.groups = json.dumps(groups)
    class_room_group_info.save()

    return lesson_env


def get_create_group_env_executor(user_id, class_group_id, group_key):
    executor = {
        'func': create_group_env,
        'params': {
            'user_id': user_id,
            'class_group_id': class_group_id,
            'group_key': group_key,
        },
        'extra': group_key,
    }
    return executor


def delete_group_env(class_room_group_info, group_key):
    groups = json.loads(class_room_group_info.groups)
    group_dict = {group['key']: group for group in groups}
    if group_key not in group_dict:
        raise exceptions.PermissionDenied()

    group = group_dict[group_key]
    lesson_env_id = group.get('lesson_env')
    if lesson_env_id:
        can_delete_status = Env.UseStatusList
        lesson_env = LessonEnv.objects.filter(pk=lesson_env_id).first()
        if lesson_env and lesson_env.env and lesson_env.env.status in can_delete_status:
            admin_delete_env(lesson_env.env)

    # 删除队列
    class_room_group_info.waits.filter(extra=group_key).delete()


def leave_group(user_id, group):
    from ..widgets.env.error import error

    group_users = group['users']
    if user_id not in group_users:
        return False

    group_users.remove(user_id)

    lesson_env_id = group.get('lesson_env')
    if lesson_env_id:
        if LessonEnv.objects.filter(pk=lesson_env_id, env__status__in=Env.ActiveStatusList).exists():
            raise exceptions.PermissionDenied(error.NO_PERMISSION)
        # lesson_env = LessonEnv.objects.filter(pk=lesson_env_id).first()
        # if lesson_env:
        #     lesson_env.group_users.remove(user_id)

    return True


def enter_group(user_id, group):
    from ..widgets.env.error import error

    group_users = group['users']
    if user_id in group_users:
        return False

    group_users.append(user_id)

    lesson_env_id = group.get('lesson_env')
    if lesson_env_id:
        if LessonEnv.objects.filter(pk=lesson_env_id, env__status__in=Env.ActiveStatusList).exists():
            raise exceptions.PermissionDenied(error.NO_PERMISSION)
        # lesson_env = LessonEnv.objects.filter(pk=lesson_env_id).first()
        # if lesson_env:
        #     lesson_env.group_users.add(user_id)

    return True


def transfer_group_user(class_room_group_info, user_id, from_group_key, to_group_key):
    from ..widgets.env.error import error

    groups = json.loads(class_room_group_info.groups)
    group_dict = {group['key']: group for group in groups}
    if from_group_key not in group_dict or to_group_key not in group_dict:
        raise exceptions.PermissionDenied(error.NO_PERMISSION)

    from_group = group_dict[from_group_key]
    leave_flag = leave_group(user_id, from_group)

    to_group = group_dict[to_group_key]
    enter_flag = enter_group(user_id, to_group)

    if leave_flag or enter_flag:
        class_room_group_info.groups = json.dumps(groups)
        class_room_group_info.save()


def add_experiment_time(user, lesson, seconds):
    try:
        if CourseUserStat.objects.filter(user=user, lesson=lesson).exists():
            CourseUserStat.objects.filter(user=user, lesson=lesson).update(
                experiment_seconds=F('experiment_seconds') + seconds,
                experiment_update_time=timezone.now(),
            )
        else:
            CourseUserStat.objects.create(
                user=user,
                lesson=lesson,
                experiment_seconds=seconds,
            )
    except:
        pass


def add_attend_class_time(user, lesson, seconds):
    try:
        now_time = timezone.now()
        stat = CourseUserStat.objects.filter(user=user, lesson=lesson).first()
        if stat:
            update_interval = (now_time - stat.attend_update_time).total_seconds()
            if update_interval < seconds:
                return

            CourseUserStat.objects.filter(user=user, lesson=lesson).update(
                attend_class_seconds=F('attend_class_seconds') + seconds,
                attend_update_time=timezone.now(),
            )
        else:
            CourseUserStat.objects.create(
                user=user,
                lesson=lesson,
                attend_class_seconds=seconds,
            )
    except:
        pass


class LessonTaskHandler(BaseTaskHandler):
    pass
