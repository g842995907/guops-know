from django.shortcuts import render

from common_framework.views import find_menu

from common_web.decorators import login_required as web_login_required
from oj import settings
from x_vulns.response import ResError

from x_vulns.setting import api_settings
from x_vulns.utils.cvss_util import gen_cvss_indicator

slug = api_settings.SLUG


@web_login_required
@find_menu(slug)
def vuln_list(request, **kwargs):
    context = kwargs.get('menu')
    context['search'] = request.GET.get('search')
    context['cn'] = request.GET.get('cn')
    context['exploit'] = request.GET.get('exploit')
    return render(request, 'x_vulns/web/vuln_list.html', context)


@web_login_required
@find_menu(slug)
def vuln_global(request, **kwargs):
    context = kwargs.get('menu')
    return render(request, 'x_vulns/web/vuln_global.html', context)


import json
import logging
from collections import OrderedDict

from rest_framework import response, status, exceptions
from rest_framework.decorators import api_view

from common_framework.utils import views as default_views
from common_framework.utils.http import HttpClient

logger = logging.getLogger()


@web_login_required
@find_menu(slug)
def vuln_detail(request, pk, **kwargs):
    context = kwargs.get('menu')
    context['pk'] = pk
    http = HttpClient(api_settings.SERVER, timeout=20)
    json_data = {
        'api_key': '123456',
        '_id': pk,
    }
    url = http.murl(api_settings.DETAIL_URL)
    try:
        res = http.mpost(url, json=json_data)
    except Exception as e:
        logger.error('get vuln detail error: %s -- data[%s] server[%s]', e.message, json_data, url)
        # return default_views.Http404Page(request, e)
        return default_views.Http404Page(request, Exception())
    res_data = http.result(res, True)
    if res.status_code != 200:
        return default_views.Http404Page(request, Exception())
    return render(request, 'x_vulns/web/vuln_detail.html', context)


@web_login_required
@api_view(['GET'])
def api_vuln_list(request, **kwargs):
    http = HttpClient(api_settings.SERVER, timeout=20)
    query_params = request.GET
    try:
        offset = int(query_params.get('offset') or 0)
        limit = int(query_params.get('limit') or 10)
        cn = query_params.get('cn')
        exploit = query_params.get('exploit')
    except:
        offset = 0
        limit = 10
        cn = ''
        exploit = ''
    page = offset / limit + 1
    json_data = {
        'api_key': '123456',
        'keyword': query_params.get('search', ''),
        'page': page,
        'per_page': limit,
        'zh': cn,
        'exploit': exploit
    }
    url = http.murl(api_settings.LIST_URL)
    try:
        res = http.mpost(url, json=json_data)
    except Exception as e:
        logger.error('get vuln list error: %s -- data[%s] server[%s]', e.message, json_data, url)
        total = 0
        data = []
    else:
        res_data = http.result(res, True)
        if res.status_code == 200:
            total = res_data.get('total_records', 0)
            data = res_data['data']
        else:
            logger.error('get vuln list error: %s -- data[%s] server[%s]', res_data.get('message'), json_data, url)
            total = 0
            data = []

    return response.Response(OrderedDict([
        ('total', total),
        ('rows', data)
    ]))


@web_login_required
@api_view(['GET'])
def api_vuln_detail(request, pk, **kwargs):
    http = HttpClient(api_settings.SERVER, timeout=20)
    json_data = {
        'api_key': '123456',
        '_id': pk,
    }
    url = http.murl(api_settings.DETAIL_URL)
    try:
        res = http.mpost(url, json=json_data)
    except Exception as e:
        logger.error('get vuln detail error: %s -- data[%s] server[%s]', e.message, json_data, url)
        # return default_views.Http404Page(request, e)
        raise exceptions.NotFound(ResError.VULN_CONNECTED_FAILED)

    res_data = http.result(res, True)
    if res.status_code == 200:
        data_list = res_data['data']
        if len(data_list) > 0:
            data = json.loads(data_list)
            if data.get('software_list') is not None:
                rows = []
                for software in data.get('software_list'):
                    rows.append(eval(software))
                data['software_list'] = rows
            cvss_data = gen_cvss_indicator(data.get('cvss'))
            data['cvss_data'] = cvss_data
        else:
            # return default_views.Http404Page(request, Exception())
            raise exceptions.NotFound(ResError.VULN_CONNECTED_FAILED)
    else:
        logger.error('get vuln detail error: %s -- data[%s] server[%s]', res_data.get('message'), json_data, url)
        # return default_views.Http404Page(request, Exception())
        raise exceptions.NotFound(ResError.VULN_CONNECTED_FAILED)

    return response.Response(data)


@web_login_required
@api_view(['GET'])
def api_vuln_global_risk(request, **kwargs):
    http = HttpClient(api_settings.SERVER, timeout=20)
    vuln_type = request.GET.get('type')
    url = http.murl('{url}?type={type}'.format(url=api_settings.GLOBAL_RISK, type=vuln_type))
    try:
        res = http.mget(url)
    except Exception as e:
        logger.error('get vuln global risk error: %s -- server[%s]', e.message, url)
        # return default_views.Http404Page(request, e)
        raise exceptions.NotFound(ResError.VULN_CONNECTED_FAILED)
    res_data = http.result(res, True)
    if res.status_code == 200:

        if len(res_data) > 0:
            data = res_data
        else:
            # return default_views.Http404Page(request, Exception())
            raise exceptions.NotFound(ResError.VULN_CONNECTED_FAILED)
    else:
        logger.error('get vuln global risk error: %s --server[%s]', res_data.get('message'), url)
        # return default_views.Http404Page(request, Exception())
        raise exceptions.NotFound(ResError.VULN_CONNECTED_FAILED)
    en_name = ['High Risk', 'Medium Risk', 'Low Risk', 'Unknown']
    if getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE) == 'en':
        for index, type_data in enumerate(data):
            type_data['name'] = en_name[index]

    return response.Response(data, status=status.HTTP_200_OK)


@web_login_required
@api_view(['GET'])
def api_vuln_global_type(request, **kwargs):
    http = HttpClient(api_settings.SERVER, timeout=20)
    vuln_type = request.GET.get('type')
    url = http.murl('{url}?type={type}&language={language}'.format(url=api_settings.GLOBAL_TYPE, type=vuln_type,
                                                                   language=getattr(request, 'LANGUAGE_CODE',
                                                                                    settings.LANGUAGE_CODE)))
    try:
        res = http.mget(url)
    except Exception as e:
        logger.error('get vuln global risk error: %s -- server[%s]', e.message, url)
        # return default_views.Http404Page(request, e)
        raise exceptions.NotFound(ResError.VULN_CONNECTED_FAILED)
    res_data = http.result(res, True)
    if res.status_code == 200:
        time = res_data['time']
        data = res_data['content']
    else:
        logger.error('get vuln global risk error: %s --server[%s]', res_data.get('message'), url)
        # return default_views.Http404Page(request, Exception())
        raise exceptions.NotFound(ResError.VULN_CONNECTED_FAILED)

    return response.Response(OrderedDict([
        ('time', time),
        ('content', data)
    ]), status=status.HTTP_200_OK)


@web_login_required
@api_view(['GET'])
def api_vuln_global_time(request, **kwargs):
    http = HttpClient(api_settings.SERVER, timeout=20)
    vuln_type = request.GET.get('type')
    url = http.murl('{url}?type={type}'.format(url=api_settings.GLOBAL_TIME, type=vuln_type))
    try:
        res = http.mget(url)
    except Exception as e:
        logger.error('get vuln global risk error: %s --server[%s]', e.message, url)
        # return default_views.Http404Page(request, e)
        raise exceptions.NotFound(ResError.VULN_CONNECTED_FAILED)
    res_data = http.result(res, True)
    if res.status_code == 200:
        time = res_data['time']
        data = res_data['content']

    else:
        logger.error('get vuln global risk error: %s --server[%s]', res_data.get('message'), url)
        # return default_views.Http404Page(request, Exception())
        raise exceptions.NotFound(ResError.VULN_CONNECTED_FAILED)

    return response.Response(OrderedDict([
        ('time', time),
        ('content', data)
    ]), status=status.HTTP_200_OK)
