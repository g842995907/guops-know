# -*- coding: utf-8 -*-
import os
import re
import base64
import json
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import auth
from django.contrib.auth import (
    REDIRECT_FIELD_NAME, login as auth_login,
)
from django.contrib.auth.models import Group
from django.contrib.auth import logout as django_logout
from django.contrib.auth.forms import (
    AuthenticationForm,
)
from django.core import signing
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.shortcuts import resolve_url
from django.urls import reverse
from django.utils import timezone
from django.utils.http import is_safe_url
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods
from rest_framework import status, permissions, response
from rest_framework.decorators import api_view, permission_classes

from common_auth.models import User
from common_framework.utils.app_url import get_home_module_urls
from common_framework.utils.license import License
from common_framework.utils.request import get_ip
from common_framework.views import find_menu
from common_product import module as common_module
from common_web.decorators import login_required
from system_configuration.cms.api import add_operate_log
from system_configuration.models import SystemConfiguration
from system_configuration.setting import api_settings
from x_person.response import REGEX
from common_framework.utils import license

slug = api_settings.SLUG


@login_required
@find_menu()
def index(request, **kwargs):
    context = kwargs.get('menu')
    return render(request, 'web/index.html', context=context)


def login(request):
    context = {}
    # if SystemConfiguration.objects.filter(key='public_register').exists():
    #     public_register = SystemConfiguration.objects.filter(key='public_register').first().value
    #     context['public_register'] = int(public_register)
    public_register = license.get_system_config("public_register")
    if public_register:
        context['public_register'] = 1 if int(public_register) != 0 else 0
    else:
        context["public_register"] = 0
    next = request.GET.get('next', '/')
    context['next'] = next
    context['show_notice'] = api_settings.SHOW_NOTICE

    return render(request, 'web/login.html', context)


def register(request):
    if SystemConfiguration.objects.filter(key='public_register').exists():
        if SystemConfiguration.objects.filter(key='public_register').first().value == '1':
            return render(request, 'web/register.html')
    return HttpResponseRedirect(reverse('common_web:login'))


@require_http_methods(['GET'])
@login_required(login_url='common_web:login')
def logout(request):
    if request.method == 'GET':
        user = request.user

        add_operate_log(user, common_module.SYSTEM,
                        'name[{}] logout system, user name [{}]'.format(user.username, user.first_name), 0,
                        _('x_system_logout').format(user.first_name), )
        django_logout(request)

        return redirect(reverse("common_web:login"))


@login_required
@find_menu()
def home(request, **kwargs):
    context = kwargs.get('menu')
    context = get_home_module_urls(context)
    if settings.PLATFORM_TYPE == 'AD':
        return redirect(reverse("x_person:index_ad"))
    # elif settings.PLATFORM_TYPE in ['OJ', 'ALL']:
    return redirect(reverse("x_person:index_new"))
    # return redirect(reverse("x_person:person"))


def forbidden(request, **kwargs):
    context = kwargs.get('menu')
    return render(request, 'web/403.html', context=context)


def not_found(request, **kwargs):
    context = kwargs.get('menu')
    return render(request, 'web/404.html', context=context)


def server_error(request, **kwargs):
    context = kwargs.get('menu')
    return render(request, 'web/500.html', context=context)


def authorization(request):
    dict_hardware_info = license.LicenseInfo().get_encrypt_info()

    context = {'hardware_info': dict_hardware_info}
    return render(request, 'web/authorization.html', context=context)


@find_menu()
def forget_password(request, **kwargs):
    context = kwargs.get('menu')
    if request.method == 'POST':
        username = request.POST.get('username', None)
        u = User.objects.filter(username=username)
        if u.exists():
            u = u.first()
            if u.email_validate:
                token = signing.dumps({"id": u.id})
                url = request.build_absolute_uri(reverse('common_web:set_password'))
                import urllib
                set_password_url = url + '?token=' + urllib.quote(token)
                email_body = u'请点击下面的链接重置您的密码：{url}'.format(url=set_password_url)
                try:
                    send_mail('重置密码', email_body, settings.DEFAULT_FROM_EMAIL,
                              [u.email])
                    context['email_send'] = True
                except:
                    context['email_send'] = False
            else:
                context['email_check'] = True

        else:
            context['user_exists'] = True
    return render(request, 'web/forget_password.html', context)


@find_menu()
def set_password(request, **kwargs):
    context = kwargs.get('menu')
    if request.method == 'GET':
        token = request.GET.get('token', None)
        try:
            u = signing.loads(token, max_age=0.5 * 3600)
            u = User.objects.filter(id=u['id'])
            if u.exists():
                u = u.first()
                auth.login(request, u)
                context['user'] = u
                return render(request, 'web/set_password.html', context)
        except signing.BadSignature:
            return render(request, 'web/forget_password.html', context)


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def license_upload(request):
    file = request.FILES.get("license", None)
    dir_path = os.path.join(settings.MEDIA_ROOT, 'personal_license')
    filename = 'license.zip'

    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    full_file_name = os.path.join(dir_path, filename)

    if os.path.exists(full_file_name):
        try:
            os.remove(full_file_name)
        except Exception as e:
            pass
    try:
        chunk = file.read()
        fileobj = open(full_file_name, 'wb')
        fileobj.write(chunk)
    except IOError:
        raise IOError
    finally:
        fileobj.close()

    cache.delete("license_expired")

    error_code, info = License().judge_authorize(full_file_name)

    if not error_code:
        cache.clear()

    return response.Response({"error_code": error_code, "info": info}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def submit_register(request):
    username = request.data.get('username')
    password = request.data.get('password')

    pattern = re.compile(unicode(REGEX.REGEX_USER))
    pattern_password = re.compile(unicode(REGEX.REGEX_PASSWORD))

    if username is None:
        error_code = 3
        info = _("x_username_not_blank")
    elif password is None:
        error_code = 4
        info = _("x_password_not_blank")
    elif not pattern.match(username):
        error_code = 3
        info = _("x_username_format_error")
    elif not pattern_password.match(password):
        error_code = 4
        info = _("x_password_format_error")
    elif User.objects.filter(username=username).exists():
        error_code = 1
        info = _("x_username_already_exists")
    else:
        captcha_key = request.data.get('captcha')
        if captcha_key == '':
            error_code = 5
            info = _('x_enter_verification_code')
        elif captcha_key.lower() == request.session.get('captcha'):
            del request.session['captcha']
            user = User.objects.create(
                username=username,
                is_staff=False,
                is_active=True,  # True正常状态
                status=User.USER.NEW_REGISTER
            )
            user.set_password(password)
            user.save()
            group = Group.objects.get(id=3)
            user.groups.add(group)
            error_code = 0
            info = _("x_registration_success")
        else:
            error_code = 2
            info = _("x_verification_code_error")
    return response.Response({
        "error_code": error_code, "info": info}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def handlerlogin(request,
                 redirect_field_name=REDIRECT_FIELD_NAME,
                 authentication_form=AuthenticationForm,
                 extra_context=None, redirect_authenticated_user=False):
    """
    Displays the login form and handles the login action.
    """
    redirect_to = request.POST.get(redirect_field_name, request.GET.get(redirect_field_name, ''))

    if redirect_authenticated_user and request.user.is_authenticated:
        redirect_to = _get_login_redirect_url(request, redirect_to)
        if redirect_to == request.path:
            raise ValueError(
                "Redirection loop for authenticated user detected. Check that "
                "your LOGIN_REDIRECT_URL doesn't point to a login page."
            )
        return HttpResponseRedirect(redirect_to)
    elif request.method == "POST":
        form = authentication_form(request, data=request.data)
        captcha = request.data.get('captcha', '')
        if captcha == '':
            return response.Response({'error_code': '7'})
        else:
            if captcha.lower() == request.session.get('captcha'):
                del request.session['captcha']
            else:
                return response.Response({'error_code': '8'})

        if form.is_valid():
            user = form.get_user()
            now = datetime.now()

            if user.expired_time is not None and now > user.expired_time:
                return response.Response({'error_code': '6'})

            auth_login(request, user)
            user.last_login_ip = get_ip(request)
            try:
                user.save()
            except Exception as e:
                pass

            add_operate_log(user, common_module.SYSTEM,
                            'name[{}] login system, login user name [{}]'.format(user.username, user.first_name), 0,
                            _('x_system_login').format(user.first_name), )

            return response.Response({'redirect_url': _get_login_redirect_url(request, redirect_to)})
        else:
            if request.data.get('username') == '' and request.data.get('password') == '':
                return response.Response({'error_code': '1'})
            elif request.data.get('username') == '':
                return response.Response({'error_code': '2'})
            elif request.data.get('password') == '':
                return response.Response({'error_code': '3'})
            else:
                if User.objects.filter(username=request.data.get('username')).exists():
                    user = User.objects.get(username=request.data.get('username'))
                    if not user.check_password(request.data.get('password')):
                        # if User.objects.filter(username=request.data.get('username')).first().is_active:
                        return response.Response({'error_code': '4'})
                    else:
                        return response.Response({'error_code': '5'})
                else:
                    return response.Response({'error_code': '4'})


def _get_login_redirect_url(request, redirect_to):
    # Ensure the user-originating redirection URL is safe.
    if not is_safe_url(url=redirect_to, host=request.get_host()):
        return resolve_url(settings.LOGIN_REDIRECT_URL)
    return redirect_to


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def report_online(request):
    if request.method == 'POST':
        user_obj = User.objects.filter(pk=request.user.id)
        if user_obj.exists() and user_obj.first().report_time:
            is_online = True if user_obj.first().report_time > (timezone.now() - timedelta(seconds=300)) else False
            if is_online:
                online_add_time = (timezone.now() - user_obj.first().report_time).total_seconds()
                user_obj.update(
                    total_online_time=(user_obj.first().total_online_time + online_add_time)
                )
            else:
                user_obj.update(total_online_time=0)

        try:
            User.objects.filter(pk=request.user.id).update(
                report_time=timezone.now()
            )
        except Exception as e:
            pass
        return response.Response({})


# def message(request):
#     if SystemConfiguration.objects.filter(key='public_register').exists():
#         if SystemConfiguration.objects.filter(key='public_register').first().value == '1':
#             return render(request, 'web/message.html')
#     return HttpResponseRedirect(reverse('common_web:login'))

@login_required
@find_menu(slug)
def message(request, **kwargs):
    context = kwargs.get('menu')
    return render(request, 'web/message.html', context)
