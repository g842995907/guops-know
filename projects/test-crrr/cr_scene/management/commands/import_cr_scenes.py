# -*- coding: utf-8 -*-
import logging
import os

from django.core.management import BaseCommand

from base.utils.error import stack_error
from cr_scene.utils.resource import import_cr_scenes


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str)

    def handle(self, *args, **options):
        files = options['files']
        for file_path in files:
            if not os.path.exists(file_path):
                logger.error('file path % not exists', file_path)
                continue

            try:
                import_cr_scenes(file_path)
            except Exception as e:
                logger.error('import cr scenes from %s error: %s', file_path, e)
                stack_error()
