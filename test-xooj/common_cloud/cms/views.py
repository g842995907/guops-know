import json

from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from common_cloud import models as cloud_models
from common_framework.utils.rest.permission import IsStaffPermission


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def department(request):
    context = {}
    return render(request, 'common_cloud/cms/department.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def department_detail(request, department_id):
    context = {
        'mode': 1,
    }

    department_id = int(department_id)
    config_list = cloud_models.LicenseConfig.objects.all()
    config_info = []
    if department_id == 0:
        context['mode'] = 0
        for config in config_list:
            license_info = {}
            license_info['cn_name'] = config.cn_name
            license_info['en_name'] = config.en_name
            license_info['type'] = config.type
            license_info['value'] = ""
            config_info.append(license_info)
        context['config_info'] = config_info
        context['json_config_info'] = json.dumps(config_info)
    else:
        department = cloud_models.Department.objects.get(id=department_id)
        context['department'] = department
        for config in config_list:
            license_info = {}
            license_info['cn_name'] = config.cn_name
            license_info['en_name'] = config.en_name
            license_info['type'] = config.type
            configuration = eval(department.license_info)
            license_info['value'] = configuration.get(config.en_name, "")
            config_info.append(license_info)
        context['config_info'] = config_info
        context['json_config_info'] = json.dumps(config_info)

    return render(request, 'common_cloud/cms/department_detail.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def update(request):
    context = {}
    return render(request, 'common_cloud/cms/update.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def update_detail(request, update_id):
    context = {
        'mode': 1,
    }

    update_id = int(update_id)
    if update_id == 0:
        context['mode'] = 0
    else:
        context['update'] = cloud_models.UpdateInfo.objects.get(id=update_id)

    return render(request, 'common_cloud/cms/update_detail.html', context)
