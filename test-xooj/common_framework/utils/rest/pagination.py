# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict

from django.conf import settings

from rest_framework import pagination, response


class BootstrapPagination(pagination.LimitOffsetPagination):
    max_limit = 1000

    def get_paginated_response(self, data):
        return response.Response(OrderedDict([
            ('total', self.count),
            ('rows', data)
        ]))

    def get_count(self, queryset, view=None):
        if view and getattr(view, 'page_cache', False):
            cache_key = view._default_generate_count_cache_key()
            count = view.cache.get(cache_key)
            if count is None:
                count = pagination._get_count(queryset)
                view.cache.set(cache_key, count, view.get_cache_age())
        else:
            count = pagination._get_count(queryset)
        return count

    def get_limit(self, request, view=None):
        if hasattr(self, 'limit'):
            return self.limit
        limit = super(BootstrapPagination, self).get_limit(request)
        if limit is None:
            if view and hasattr(view, 'unlimit_pagination') and view.unlimit_pagination:
                limit = 999999
            else:
                limit = self.max_limit
            request.query_params._mutable = True
            request.query_params[self.limit_query_param] = limit
            request.query_params._mutable = False
        return limit

    def paginate_queryset_flag(self, queryset, request, view=None):
        self.queryset = queryset
        self.limit = self.get_limit(request, view)
        self.offset = self.get_offset(request)
        self.count = self.get_count(queryset, view=view)
        self.request = request
        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        if self.count == 0 or self.offset > self.count:
            return []

        queryset = queryset[self.offset:self.offset + self.limit]
        if view and getattr(view, 'page_cache', False):
            self.page_queryset = queryset
            view.cache_key = view.get_cache_key()

        return True