import math

from rest_framework import response, status
from rest_framework.utils.urls import replace_query_param


def to_error(code, message):
    return {
        'error_code': code,
        'error_message': message
    }


ILLEGAL_REQUEST_PARAMETERS = to_error(0x0010, 'illegal request parameters')


def list_view(request, queryset, serializer):
    try:
        per_page = int(request.query_params.get("per_page", 10))
        page = int(request.query_params.get("page", 1))
    except Exception:
        per_page = 10
        page = 1
    total = len(queryset)
    start = (page - 1) * per_page + 1
    current_page = page
    end = start + per_page - 1
    last_page = int(math.ceil(total * 1.0 / per_page))
    queryset = queryset[per_page * (page - 1):per_page * page]
    pagination = {
        "current_page": current_page,
        "total": total,
        "from": start,
        "to": end,
        "last_page": last_page,
        "next_page_url": get_next_link(request, page, per_page, total),
        "perv_page_url": get_previous_link(request, page, current_page)
    }
    links = {"pagination": pagination}
    data = [serializer(row).data for row in queryset]

    return response.Response({'links': links, 'data': data}, status=status.HTTP_200_OK)


def get_next_link(request, page, per_page, total):
    if page * per_page >= total:
        return None
    url = request.build_absolute_uri()
    return replace_query_param(url, "page", page + 1)


def get_previous_link(request, page, current_page):
    if current_page == 1:
        return None
    url = request.build_absolute_uri()
    return replace_query_param(url, "page", page - 1)
