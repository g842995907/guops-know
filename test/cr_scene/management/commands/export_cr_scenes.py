# -*- coding: utf-8 -*-
import logging

from django.core.management import BaseCommand

from base.utils.error import stack_error
from cr_scene.models import CrScene
from cr_scene.utils.resource import export_cr_scenes


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('ids', nargs='+', type=str)

    def handle(self, *args, **options):
        ids = options['ids']
        if ids and ids[0] == 'all':
            cr_scenes = CrScene.objects.all()
        else:
            cr_scenes = CrScene.objects.filter(id__in=ids)

        if cr_scenes:
            try:
                file_path = export_cr_scenes(cr_scenes)
            except Exception as e:
                logger.error('export cr scenes error: %s', e)
                stack_error()
            else:
                logger.info('export cr scenes to %s', file_path)
        else:
            logger.info('no cr scenes export')
