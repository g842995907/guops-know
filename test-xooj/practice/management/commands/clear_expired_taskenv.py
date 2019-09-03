# -*- coding: utf-8 -*-
import logging

from django.core.management import BaseCommand
from django.utils import timezone

from common_env.models import Env
from common_env.handlers import EnvHandler
from common_framework.utils import delay_task

from practice.base_models import TaskEnv

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            expired_task_envs = TaskEnv.objects.exclude(
                env=None
            ).filter(
                env__status__in=Env.ActiveStatusList,
                destroy_time__lte=timezone.now()
            )

            for task_env in expired_task_envs:
                try:
                    env_handler = EnvHandler(task_env.env.user)
                    env_handler.delete_env(task_env.env)
                    logger.info('clear expired task env[task_env_id=%s, env_id=%s] ok' % (task_env.id, task_env.env.id))
                except Exception as e:
                    logger.error('clear expired task env[task_env_id=%s, env_id=%s] error: %s' % (
                    task_env.id, task_env.env.id, str(e)))

        except Exception as e:
            logger.error('clear expired task env error: %s' % str(e))
