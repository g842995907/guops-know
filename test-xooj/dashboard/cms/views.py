# -*- coding: utf-8 -*-
import datetime

from django.db.models import Q, Sum
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from course.models import Lesson
from common_auth.models import User, Team, Classes
from common_auth.setting import api_settings as auth_api_settings
from common_env.models import Env, StandardDevice
from common_framework.utils.constant import Status
from common_framework.utils.rest.permission import IsStaffPermission
from common_framework.utils.shortcuts import AppRender
from common_scene.clients import nova_client, neutron_client, cinder_client, zun_client
from common_scene.setting import api_settings
from practice.api import practice_config, PRACTICE_TYPE_THEORY, \
    PRACTICE_TYPE_REAL_VULN, PRACTICE_TYPE_EXCRISE, PRACTICE_TYPE_ATTACK_DEFENSE
from practice.models import PracticeSubmitSolved
import json
from common_proxy.nginx import is_port_open
from dashboard.setting import api_settings as dashboard_api_settings
from dashboard.models import SystemUseStatus
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from event import models as event_models

from practice_real_vuln.models import RealVulnTask as RealVulnTask_models
from practice_theory.models import ChoiceTask as ChoiceTask_models
from practice_exercise.models import PracticeExerciseTask as PracticeExerciseTask_models
from practice_attack_defense.models import PracticeAttackDefenseTask
from practice.constant import TaskStatus
from common_framework.utils.rest.list_view import list_view
from system_configuration.models import UserAction


render = AppRender('dashboard', 'cms').render
cpu_allocation_ratio = api_settings.COMPLEX_MISC.get("cpu_allocation_ratio", 16.0)
ram_allocation_ratio = api_settings.COMPLEX_MISC.get("ram_allocation_ratio", 1.5)
disk_allocation_ratio = api_settings.COMPLEX_MISC.get("disk_allocation_ratio", 1.0)


class Hypervisor(object):
    _attrs = ['cpu_info', 'host_ip', 'human_id', 'hypervisor_hostname',
              'hypervisor_type', 'id', 'memory_mb', 'memory_mb_used',
              'running_vms', 'state', 'status', 'vcpus', 'vcpus_used',
              'local_gb', 'local_gb_used']
    _hypervisor = None

    def __init__(self, hypervisor):
        self._hypervisor = hypervisor

    def to_dict(self):
        obj = {}
        for key in self._attrs:
            obj[key] = getattr(self._hypervisor, key, None)
        return obj


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def dashboard(request):
    context = {}

    # dashboard summary
    user_count = User.objects.exclude(status=Status.DELETE).count()
    class_list = Classes.objects.all()
    context.update({"class_list": class_list})
    practice_count = 0
    if settings.PLATFORM_TYPE == 'AD':
        from practice_attack_defense.models import PracticeAttackDefenseTask as PracticeAttackDefense_models
        # 队伍数量
        team_count = Team.objects.filter(status=1).count()
        # 理论赛数量
        theory_base_count = ChoiceTask_models.objects.exclude(is_copy=1).count()

        # 攻防赛数量
        duoqigongfang_count = PracticeAttackDefense_models.objects.exclude(is_copy=1).count()

        duoqijieti_count = PracticeExerciseTask_models.objects.exclude(is_copy=1).count()
        realvuln_count = RealVulnTask_models.objects.exclude(is_copy=1).count()
        context.update(
            {"summary": {
                "user_count": user_count,
                "team_count": team_count,
                "duoqigongfang_count": duoqigongfang_count,
                "theory_base_count": theory_base_count,
                "duoqijieti_count": duoqijieti_count,
                "realvuln_count": realvuln_count,
                'type': 'AD',
            }}
        )

    elif settings.PLATFORM_TYPE == 'OJ':
        from course import models as course_models
        # 理论课的数量
        lilunke_count = course_models.Lesson.objects.filter(type=0, status=1).count()

        # 实验课的数量
        shiyanke_count = course_models.Lesson.objects.filter(type=1, status=1).count()

        if practice_config.get(PRACTICE_TYPE_THEORY) is not None:  # 判断模块是否存在
            # 理论基础的数量
            theory_base_count = ChoiceTask_models.objects.exclude(is_copy=1).count()

        if practice_config.get(PRACTICE_TYPE_EXCRISE) is not None:
            # 夺旗解题的数量
            duoqijieti_count = PracticeExerciseTask_models.objects.exclude(is_copy=1).count()

        if practice_config.get(PRACTICE_TYPE_REAL_VULN) is not None:
            # 真实漏洞的数量
            realvuln_count = RealVulnTask_models.objects.exclude(is_copy=1).count()

        context.update(
            {"summary": {
                "user_count": user_count,
                "lilunke_count": lilunke_count,
                "shiyanke_count": shiyanke_count,
                "theory_base_count": theory_base_count,
                "duoqijieti_count": duoqijieti_count,
                "realvuln_count": realvuln_count,
                'type': 'OJ',
            }}
        )

    else:
        from practice.models import TaskEvent
        practice_count = TaskEvent.objects.count()

        std_count = StandardDevice.objects.filter().count()
        env_count = Env.objects.filter(status=Env.Status.TEMPLATE).count()
        context.update(
            {"summary": {
                "user_count": user_count,
                "practice_count": practice_count,
                # "event_count": event_count,
                "scene_count": std_count,
                "env_count": env_count,
                'type': 'ALL',
            }}
        )

    # dongtai
    task_envs = Env.objects.all().order_by('-id')[:5]
    context.update({"task_envs": task_envs})

    return render(request, 'dashboard.html', context=context)


def hyperv_stats(request):
    # openstack hypervisor
    hyperv_list = []
    try:
        instance_count = 0
        vcpu_percent = 0.0
        ram_percent = 0.0
        disk_percent = 0.0
        instance_max = 100
        nv_client = nova_client.Client(project_name="admin")
        hypers = nv_client.hypervisor_list()

        for hyper in hypers:
            hyperv_list.append(Hypervisor(hyper).to_dict())
            instance_count += hyper.running_vms
            vcpu_percent += float(hyper.vcpus_used) / float(hyper.vcpus)
            ram_percent += float(hyper.memory_mb_used) / float(hyper.memory_mb)
            disk_percent += float(hyper.local_gb_used) / float(hyper.local_gb)

        hyper_count = len(hypers)
    except Exception, e:
        return JsonResponse({})

    return JsonResponse({
        "cluster_state": {
            "vms": instance_count,
            "vm_max": instance_max,
            "vcpu": vcpu_percent / hyper_count * 100 / cpu_allocation_ratio,
            "ram": ram_percent / hyper_count * 100 / ram_allocation_ratio,
            "disk": disk_percent / hyper_count * 100 / disk_allocation_ratio,
        },
        "hypervisors": hyperv_list})



@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def get_hyper_list(request):
    try:
        hyperv_list = []
        instance_count = 0
        vcpu_percent = 0.0
        ram_percent = 0.0
        disk_percent = 0.0
        instance_max = 100
        container_max = 500
        zun_error = False
        zn_client = zun_client.Client()
        container_list = []
        try:
            # 获取所有容器
            container_list = zn_client.container_list()
        except Exception, e:
            zun_error = True

        nv_client = nova_client.Client(project_name="admin")
        hypers = nv_client.hypervisor_list()
        for hyper in hypers:
            container_count = 0
            local_containers_count = 0
            instance_count += hyper.running_vms
            hyper.vcpus = hyper.vcpus * cpu_allocation_ratio
            hyper.vcpus_percent = float(hyper.vcpus_used) / float(hyper.vcpus)
            vcpu_percent += hyper.vcpus_percent
            hyper.memory_mb = hyper.memory_mb * ram_allocation_ratio
            hyper.ram_percent = float(hyper.memory_mb_used) / float(hyper.memory_mb)
            ram_percent += hyper.ram_percent
            hyper.local_gb = hyper.local_gb * disk_allocation_ratio
            hyper.disk_percent = float(hyper.local_gb_used) / float(hyper.local_gb)
            disk_percent += hyper.disk_percent

            for container in container_list:
                if container.host == hyper.hypervisor_hostname:
                    container_count += 1

            if hyper.hypervisor_hostname.startswith("controller"):
                from common_scene.cms.views import get_local_dockers
                local_containers_count = len(get_local_dockers())

            hyper_dict = Hypervisor(hyper).to_dict()
            hyper_dict['container_count'] = container_count + local_containers_count
            hyper_dict['vcpus_percent'] = round(hyper.vcpus_percent * 100)
            hyper_dict['ram_percent'] = round(hyper.ram_percent * 100)
            hyper_dict['disk_percent'] = round(hyper.disk_percent * 100)
            hyperv_list.append(hyper_dict)
        hyper_count = len(hypers)
    except Exception, e:
        raise e
    return list_view(request, hyperv_list, hyperListSerializer)


def platform_stats(request):
    now = datetime.datetime.now()
    user_reg_statistic = []
    team_reg_statistic = []
    event_answered_statistic = []
    course_learned_statistic = []
    practise_studyed_statistic = []
    x_axis = []
    for i in range(30)[::-1]:
        n_day = now - datetime.timedelta(days=i)
        x_axis.append(n_day.strftime('%Y-%m-%d'))
        n_day_start = datetime.datetime.strptime(n_day.strftime('%Y-%m-%d 00:00:00'), '%Y-%m-%d %H:%M:%S')
        n_day_end = datetime.datetime.strptime(n_day.strftime('%Y-%m-%d 23:59:59'), '%Y-%m-%d %H:%M:%S')
        user_reg_statistic.append(User.objects.filter(date_joined__range=(n_day_start, n_day_end)).count())
        team_reg_statistic.append(Team.objects.filter(create_time__range=(n_day_start, n_day_end)).count())
        event_answered_statistic.append(
            event_models.EventUserAnswer.objects.filter(time__range=(n_day_start, n_day_end)).count())
        try:
            from course.models import Record
            course_learned_statistic.append(Record.objects.filter(start_time__range=(n_day_start, n_day_end)).count())
        except:
            pass

        practise_studyed_statistic.append(
            PracticeSubmitSolved.objects.filter(submit_time__range=(n_day_start, n_day_end)).count())
    if settings.PLATFORM_TYPE == 'AD':
        return JsonResponse({"user_reg": {"x_axis": x_axis, "data": user_reg_statistic},
                             "team_reg": {"data": team_reg_statistic},
                             "event_answered": {"data": event_answered_statistic},
                             "sys_type": {"data": 'AD'}
                             })
    # OJ 和 ALL
    else:
        return JsonResponse({"user_reg": {"x_axis": x_axis, "data": user_reg_statistic},
                             "course_learn": {"data": course_learned_statistic},
                             "practise_study": {"data": practise_studyed_statistic},
                             "sys_type": {"data": 'OJ'}
                             })


# 获取cpu,内存,硬盘使用情况
def system_stats(request):
    x_axis = []
    cpu = []
    ram = []
    disk = []

    datas = SystemUseStatus.objects.order_by("-alert_time")[:100:-1]
    for data in datas:
        x_axis.append(datetime.datetime.strftime(data.alert_time, "%Y-%m-%d %H:%M:%S"))
        cpu.append(round(float(data.vcpu)))
        ram.append(round(float(data.ram)))
        disk.append(round(float(data.disk)))

    return JsonResponse({"x_axis": {"data": x_axis},
                         "cpu": {"data": cpu},
                         "ram": {"data": ram},
                         "disk": {"data": disk},
                         "sys_type": {"data": 'OJ'}
                         })


# 获取平台用户,课时,练习,场景,在线人数
@api_view(['GET'])
def get_system_state(request):
    class_number = Classes.objects.filter(status=Status.NORMAL).count()

    online_list = []
    for obj in User.objects.all():
        if obj.report_time:
            critical_time = timezone.now() - datetime.timedelta(seconds=auth_api_settings.OFFLINE_TIME)
            if obj.report_time >= critical_time:
                online_list.append(obj)

    active_scene = Env.objects.filter(status__in=Env.UsingStatusList).count()

    # 管理员 学员 教员
    users = User.objects.all().exclude(status=User.USER.DELETE)
    admin_nums = users.filter(Q(groups__name='管理员') | Q(groups__name='x_administrator')
                              | Q(groups__name='Administrator') | Q(is_superuser=1)).count()
    teacher_nums = users.filter(Q(groups__name='教员') | Q(groups__name='x_teacher') | Q(groups__name='Teacher')).count()
    student_nums = users.filter(Q(groups__name='学员') | Q(groups__name='x_student') | Q(groups__name='Student')).count()
    user_data = {
        "title": _('x_user'),
        "legend": [_('x_student') + ':' + str(student_nums),
                   _('x_teacher') + ':' + str(teacher_nums),
                   _('x_administrator') + ':' + str(admin_nums)],
        "value": [
            {"value": student_nums, "name": _('x_student') + ':' + str(student_nums)},
            {"value": teacher_nums, "name": _('x_teacher') + ':' + str(teacher_nums)},
            {"value": admin_nums, "name": _('x_administrator') + ':' + str(admin_nums)}
        ]
    }

    theory_task = Lesson.objects.filter(type=Lesson.Type.THEORY, status=Status.NORMAL)
    experiment_task = Lesson.objects.filter(type=Lesson.Type.EXPERIMENT, status=Status.NORMAL)
    lesson_data = {
        "title": _('x_lesson_num'),
        "legend": [_('x_heoretical_lesson') + ':' + str(theory_task.count()),
                   _('x_experiment_course') + ':' + str(experiment_task.count())],
        "value": [
            {"value": theory_task.count(), "name": _('x_heoretical_lesson') + ':' + str(theory_task.count())},
            {"value": experiment_task.count(), "name": _('x_experiment_course') + ':' + str(experiment_task.count())},
        ]
    }

    if practice_config.get(PRACTICE_TYPE_THEORY) is not None:
        practice_theory = ChoiceTask_models.objects.exclude(is_copy=1).exclude(status=TaskStatus.DELETE)

    if practice_config.get(PRACTICE_TYPE_EXCRISE) is not None:
        practice_exercise = PracticeExerciseTask_models.objects.exclude(is_copy=1).exclude(status=TaskStatus.DELETE)

    if practice_config.get(PRACTICE_TYPE_REAL_VULN) is not None:
        practice_realvuln = RealVulnTask_models.objects.exclude(is_copy=1).exclude(status=TaskStatus.DELETE)

    if practice_config.get(PRACTICE_TYPE_ATTACK_DEFENSE) is not None:
        practice_attack_defense = PracticeAttackDefenseTask.objects.exclude(is_copy=1).exclude(status=TaskStatus.DELETE)

    exercise_data_ad = {
        "title": _('x_practice'),
        "legend": [_('x_theory') + ':' + str(practice_theory.count()),
                   _('x_exercise') + ':' + str(practice_exercise.count()),
                   _('x_real_vuln') + ':' + str(practice_realvuln.count()),
                   _('x_ad_mode') + ':' + str(practice_attack_defense.count())],
        "value": [
            {"value": practice_theory.count(), "name": _('x_theory') + ':' + str(practice_theory.count())},
            {"value": practice_exercise.count(), "name": _('x_exercise') + ':' + str(practice_exercise.count())},
            {"value": practice_realvuln.count(), "name": _('x_real_vuln') + ':' + str(practice_realvuln.count())},
            {"value": practice_attack_defense.count(), "name": _('x_ad_mode') + ':' + str(practice_attack_defense.count())}
        ]
    }
    exercise_data_oj = {
        "title": _('x_practice'),
        "legend": [_('x_theory') + ':' + str(practice_theory.count()),
                   _('x_exercise') + ':' + str(practice_exercise.count()),
                   _('x_real_vuln') + ':' + str(practice_realvuln.count())],
        "value": [
            {"value": practice_theory.count(), "name": _('x_theory') + ':' + str(practice_theory.count())},
            {"value": practice_exercise.count(), "name": _('x_exercise') + ':' + str(practice_exercise.count())},
            {"value": practice_realvuln.count(), "name": _('x_real_vuln') + ':' + str(practice_realvuln.count())}
        ]
    }

    # 场景，标靶（虚拟机,容器）
    scene_list = Env.objects.all().filter(status=Env.Status.TEMPLATE)
    target_list = StandardDevice.objects.exclude(status=Status.DELETE)
    scene_data = {
        "title": _('x_scene'),
        "legend": [_('x_scene') + ':' + str(scene_list.count()),
                   _('x_instances') + ':' + str(target_list.filter(image_type=StandardDevice.ImageType.VM).count()),
                   _('x_docker_instances') + ':' + str(target_list.filter(image_type=StandardDevice.ImageType.DOCKER).count())],
        "value": [
            {"value": scene_list.count(), "name": _('x_scene') + ':' + str(scene_list.count())},
            {"value": target_list.filter(image_type=StandardDevice.ImageType.VM).count(),
             "name": _('x_instances') + ':' + str(target_list.filter(image_type=StandardDevice.ImageType.VM).count())},
            {"value": target_list.filter(image_type=StandardDevice.ImageType.DOCKER).count(),
             "name": _('x_docker_instances') + ':' + str(target_list.filter(image_type=StandardDevice.ImageType.DOCKER).count())},
        ]
    }

    if settings.PLATFORM_TYPE == 'AD':
        return JsonResponse({
            "user_data": user_data,
            "exercise_data": exercise_data_ad,
            "scene_data": scene_data,
            "online_user": len(online_list),
            "active_scene": active_scene,
            "class_number": class_number,
            "type": "AD"
        })
    else:
        return JsonResponse({
            "user_data": user_data,
            "lesson_data": lesson_data,
            "exercise_data": exercise_data_oj,
            "scene_data": scene_data,
            "online_user": len(online_list),
            "active_scene": active_scene,
            "class_number": class_number,
            "type": "OJ"
        })


# 在线用户监控
@api_view(['GET'])
def online_user_monitor(request):
    online_list = []
    for obj in User.objects.all():
        if obj.report_time:
            critical_time = timezone.now() - datetime.timedelta(seconds=auth_api_settings.OFFLINE_TIME)
            if obj.report_time >= critical_time:
                online_list.append(obj)
    user_queryset = User.objects.filter(id__in=[user.id for user in online_list])
    user_list = user_queryset.values('id', 'username', 'first_name', 'classes__name', 'faculty__name', 'major__name', 'total_online_time')
    for user in user_list:
        user['action'], user['learn_object'] = get_recent_action(user['id'])
        user['monitor'], user['lesson_id'] = judge_monitor(user['id'])

    # rows = [OnlineUserSerializer(row).data for row in user_list]
    # return JsonResponse({"total": len(rows), "rows": rows})

    return list_view(request, user_list, OnlineUserSerializer)


class OnlineUserSerializer(object):
    def __init__(self, row):
        self.data = {
            'user_id': row.get('id'),
            'lesson_id': row.get('lesson_id'),
            'username': row.get('username'),
            'first_name': row.get('first_name'),
            'action': row.get('action', None),
            'learn_object': row.get('learn_object', None),
            'total_online_time': row.get('total_online_time', 0),
            'monitor': row.get('monitor', False)
        }
        organization = '/'.join([
            row.get('faculty__name'),
            row.get('major__name'),
            row.get('classes__name')
        ]) if not type(row.get('faculty__name')) == type(None) else None

        self.data['organization'] = organization


def get_recent_action(id):
    recent_action = UserAction.objects.filter(user=id).last()
    if recent_action:
        action = recent_action.content[0:2]
        if action == '考试':
            learn_object = recent_action.content.split('：')[1]
        else:
            learn_object = recent_action.content[2:]
        return action, learn_object
    else:
        return None, None


def judge_monitor(id):
    recent_action = UserAction.objects.filter(user=id).last()
    if recent_action:
        learn_type = recent_action.content.split('/')[0].split('：')[0]
        course_name = recent_action.content.split('/')[0].split('：')[1]
        if learn_type == '考试':
            return None, None
        lesson_name = recent_action.content.split('/')[1]
        if learn_type[2:4] == '课程':
            lesson_obj = Lesson.objects.filter(course__name=course_name).filter(name=lesson_name).exclude(status=Status.DELETE)
            if lesson_obj.exists() and lesson_obj.first().type == Lesson.Type.EXPERIMENT:
                if lesson_obj.first().envs.all().filter(env__status__in=Env.UsingStatusList).exists():
                    return True, lesson_obj.first().id
                else:
                    return False, lesson_obj.first().id
    return False, None


def get_alarm(request):
    try:
        # 获取系统配置里面的告警值
        cpu_alarm_percent = dashboard_api_settings.ALARM_PERCENT.get("cpu_alarm_percent", 80)
        ram_alarm_percent = dashboard_api_settings.ALARM_PERCENT.get("ram_alarm_percent", 80)
        disk_alarm_percent = dashboard_api_settings.ALARM_PERCENT.get("disk_alarm_percent", 80)

        res = hyperv_stats(request)
        alarm_list = get_service_alarm_list()
        # 如果所有服务正常，再获取资源告警
        if len(alarm_list) == 0:
            source_rate = json.loads(res.content)['cluster_state']
            disk_rate = source_rate['disk']
            cpu_rate = source_rate['vcpu']
            ram_rate = source_rate['ram']

            if disk_rate > disk_alarm_percent:
                rate_dict = {
                    'service': '磁盘使用率过高',
                    'state': round(disk_rate, 1),
                }

                alarm_list.append(rate_dict)

            if cpu_rate > cpu_alarm_percent:
                rate_dict = {
                    'service':  'cpu使用率过高',
                    'state': round(cpu_rate, 1),
                }
                alarm_list.append(rate_dict)

            if ram_rate > ram_alarm_percent:
                rate_dict = {
                    'service':  '内存使用率过高',
                    'state': round(ram_rate, 1),
                }
                alarm_list.append(rate_dict)

        al_list = json.dumps(alarm_list)
        context = {}
        context['alarm_list'] = al_list

    except Exception, e:
        return JsonResponse({})
    return JsonResponse(context)


# 获取所有异常的服务
def get_service_alarm_list():
    try:
        service_list = []
        # 获取 httpd服务端口
        httpd_port = api_settings.defaults.get('CONTROLLER_HTTPD_PORT', 80)
        # 判断服务端口是否打开
        memcache_hosts = api_settings.COMPLEX_MISC.get("memcache_host")
        memcached_bool = True
        for host in memcache_hosts:
            if ":" in host:
                ip, port = host.split(":")
                if not is_port_open(ip, port):
                    memcached_bool = False
                    break
        rabbitmq_bool = is_port_open('controller', 5672)
        glance_api_bool = is_port_open('controller', 9292)
        glance_registry_bool = is_port_open('controller', 9191)
        keystone_bool = is_port_open('controller', 35357)
        httpd_bool = is_port_open('controller', httpd_port)

        if memcached_bool is not True:
            service_list.append({'service': 'Memcached', 'state': 'down'})

        if rabbitmq_bool is not True:
            service_list.append({'service': 'Rabbitmq', 'state': 'down'})

        if glance_api_bool is not True:
            service_list.append({'service': 'Glance', 'state': 'down'})

        if glance_registry_bool is not True:
            service_list.append({'service': 'Glance', 'state': 'down'})

        if keystone_bool is not True:
            service_list.append({'service': 'Keystone', 'state': 'down'})

        if httpd_bool is not True:
            service_list.append({'service': 'Openstack Dashboard', 'state': 'down'})

        # 获取 nova 服务告警,先判断nova-api
        nova_api_bool = is_port_open('controller', 8775)
        if nova_api_bool is True:
            nv_client = nova_client.Client(project_name="admin")
            nova_list = list(nv_client.service_list())
            for item in nova_list:
                if item.state != 'up':
                    # if item.binary == 'nova-compute':
                    #     service = '计算'
                    # elif item.binary == 'nova-scheduler':
                    #     service = '调度'
                    # elif item.binary == 'nova-conductor':
                    #     service = 'nova数据库操作'
                    # elif item.binary == 'nova-consoleauth':
                    #     service = 'nova实例控制台'
                    service = 'Host:'+item.host+' Nova'
                    nova_dict = {
                        'service': service,
                        'state': item.state,
                    }
                    service_list.append(nova_dict)
                    break
        else:
            service_list.append({'service': 'Nova', 'state': 'down'})

        # 获取 neutron 服务告警
        network_client = neutron_client.Client(project_name="admin")
        network_list = network_client.agent_list()['agents']

        for item in network_list:
            if item['alive'] is not True:
                # if item['binary'] == 'neutron-dhcp-agent':
                #     service = 'dhcp'
                # elif item['binary'] == 'neutron-metadata-agent':
                #     service = 'metadata-agent'
                # elif item['binary'] == 'neutron-l3-agent':
                #     service = 'l3-agent'
                # elif item['binary'] == 'neutron-linuxbridge-agent':
                #     service = 'linuxbridge'
                service = 'Host:' + item['host']+' Neutron'
                network_dict = {
                    'service': service,
                    'state': str(item['alive']),
                }
                service_list.append(network_dict)
                break

        # 获取cinder服务告警
        # cin_client = cinder_client.Client(project_name="admin")
        # cinder_list = cin_client.service_list()

        # service_list.append({'service': 'nova_test', 'state': 'DOWN'})
        # 获取zun 服务告警,先判断zun-api

        zun_api_bool = is_port_open('controller', 9517)
        if zun_api_bool is True:

            zn_client = zun_client.Client(project_name="admin")
            zun_list = zn_client.service_list()
            for item in zun_list:
                if item.state != 'up':
                    service = 'Host:' + item.host+'Container'
                    zun_dict = {
                        'service': service,
                        'state': str(item.state),
                    }
                    service_list.append(zun_dict)
                    break

        else:
            service_list.append({'service': 'zun', 'state': 'down'})
    except Exception, e:
        pass

    return service_list


class hyperListSerializer(object):
    def __init__(self, row):
        self.data = {
            'container_count': row.get('container_count'),
            'vcpus_percent': row.get('vcpus_percent'),
            'ram_percent': row.get('ram_percent'),
            'disk_percent': row.get('disk_percent'),
            'hypervisor_hostname': row.get('hypervisor_hostname'),
            'host_ip': row.get('host_ip'),
            'running_vms': row.get('running_vms'),
            'state': row.get('state'),
            'status': row.get('status'),
        }
