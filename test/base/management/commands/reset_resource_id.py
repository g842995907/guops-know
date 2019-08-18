# -*- coding: utf-8 -*-
import logging

from django.core.management import BaseCommand
from django.utils import six
from django.utils.module_loading import import_string

from base.utils.resource.models import resource_classes
from base.utils.text import rk


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('models', nargs='+', type=str)

    def handle(self, *args, **options):
        model_classes = options['models']
        if model_classes and model_classes[0] == 'all':
            model_classes = resource_classes

        for model_class in model_classes:
            if isinstance(model_class, six.string_types):
                model_class = import_string(model_class)
            manager = getattr(model_class, 'original_objects', model_class.objects)
            for obj in manager.all():
                obj.resource_id = rk()
                obj.save()
