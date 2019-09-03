# -*- coding:utf-8 -*-

from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from system_configuration.models import SystemConfiguration
from common_auth.models import User

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object


class ProcessRequestsMiddleware(MiddlewareMixin):

    def process_request(self, request):
        # 新注册用户登录
        if request.user.username in [u'', u'admin', u'root']:
            return None
        elif request.user.status == User.USER.PASS:
            return None

        # 退出或者我的资料
        elif request.path in [reverse('x_person:info'),reverse('common_web:logout')]\
             or 'x_person/send_validate_email' in request.path:
            return None
        elif request.user.status == User.USER.NEW_REGISTER:
            if self.handlerUrl(request.path):
                return None
            else:
                return HttpResponseRedirect(reverse('x_person:info'))

        # 未审核用户
        elif request.user.status == User.USER.NORMAL:
            # 需要审核
            if SystemConfiguration.objects.filter(key='audit').exists():
                if SystemConfiguration.objects.filter(key='audit').first().value == '1':
                    if self.handlerUrl(request.path):
                        return None
                    else:
                        return HttpResponseRedirect(reverse('x_person:info'))
                # 不需要审核
                else:
                    return None
            else:
                pass
        # 正常
        else:
            return None

    def handlerUrl(self,path):
        urlList = ['x_person/api/', 'common_env/using_env_objects/',\
                   'message/api/','system_configuration/api' \
                   , 'jsi18n', 'static','x_person/email_validate'\
                   ,'set_password','media/user_logo','i18n/setlang']
        for url in urlList:
            if url in path:
                return True
        return False

