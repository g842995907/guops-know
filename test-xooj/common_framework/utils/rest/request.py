# -*- coding: utf-8 -*-
from common_framework.utils.list import listfilter, valuefilter


class DataFilter(object):

    def __init__(self, data):
        self.data = data

    def get(self, field_name, filter_param=unicode):
        data = self.data.get(field_name)
        return valuefilter(data, filter_param)

    def getlist(self, field_name, filter_param=unicode):
        data = self.data.getlist(field_name)
        return listfilter(data, filter_param)


class RequestData(object):

    def __init__(self, request, is_query=False, data_filter_class=DataFilter):
        self.request = request
        if is_query:
            self.data = request.query_params
        else:
            self.data = request.data
        self.data_filter = data_filter_class(self.data)

    def get(self, field_name, filter_param=unicode):
        return self.data_filter.get(field_name, filter_param)

    def getlist(self, field_name, filter_param=unicode):
        return self.data_filter.getlist(field_name, filter_param)

    def remove_field(self, field_name):
        self.data._mutable = True
        del self.data[field_name]
        self.data._mutable = False