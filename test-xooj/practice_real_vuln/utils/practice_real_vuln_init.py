# -*- coding: utf-8 -*-

from practice_real_vuln import models as real_vuln_models


def practice_real_vuln_init():
    task_list = real_vuln_models.RealVulnTask.original_objects.exclude(create_user__username__in=['admin', 'root'])
    for task in task_list:
        if task.file:
            task.file.delete()
        task.delete()
    #real_vuln_models.RealVulnCategory.objects.all().delete()
