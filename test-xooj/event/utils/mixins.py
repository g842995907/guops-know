# -*- coding: utf-8 -*-

from common_framework.utils.app import get_app_settings
from common_framework.utils.rest.mixins import RequestDataMixin


class ProductMixin(RequestDataMixin):
    
    def __init__(self, *args, **kwargs):
        super(ProductMixin, self).__init__(*args, **kwargs)
        self.extra_attr = type('ExtraAttr', (object,), {})()
        app_settings = get_app_settings(self)
        if hasattr(app_settings, 'EVENT_TYPE'):
            self.event_type = app_settings.EVENT_TYPE
            self.init_type_queryset()

    def init_type_queryset(self):
        pass
