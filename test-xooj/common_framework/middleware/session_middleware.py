# -*- coding:utf-8 -*-

from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware

from common_framework.utils.request import get_ip
from common_framework.utils.views import Http403Page
import logging

logger = logging.getLogger(__name__)


class XSessionMiddleware(SessionMiddleware):
    def process_request(self, request):
        super(XSessionMiddleware, self).process_request(request)
        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME)

        request_ip = get_ip(request)
        # 判断ip， 防止arp攻击
        if session_key is not None:
            data = request.session.load()
            logger.debug("ip:[%s]", data.get('ip'))
            session_ip = data.get('ip')

            if request_ip and session_ip and request_ip != session_ip:
                return Http403Page(request, Exception())

        request.session.ip = get_ip(request)
