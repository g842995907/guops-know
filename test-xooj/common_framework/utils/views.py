
from django.views import defaults


class Http404Page(object):

    def __new__(cls, request, exception):
        return defaults.page_not_found(request, exception, template_name='web/404.html')


class Http403Page(object):

    def __new__(cls, request, exception):
        return defaults.permission_denied(request, exception, template_name='web/403.html')


class Http400Page(object):

    def __new__(cls, request, exception):
        return defaults.bad_request(request, exception)


class Http500Page(object):

    def __new__(cls, request):
        return defaults.server_error(request, template_name='web/500.html')
