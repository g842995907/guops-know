from rest_framework.filters import OrderingFilter


class BootstrapOrderFilter(OrderingFilter):
    ordering_param = "sort"
    order = "order"

    def get_ordering(self, request, queryset, view):
        params = request.query_params.get(self.ordering_param)
        if params:
            fields = [param.strip() for param in params.split(',')]
            ordering = self.remove_invalid_fields(queryset, fields, view, request)
            if ordering:
                order = request.query_params.get(self.order)
                if order == "desc":
                    return ["-" + d for d in ordering]
                else:
                    return ordering

        # No ordering was included, or all the ordering fields were invalid
        return self.get_default_ordering(view)
