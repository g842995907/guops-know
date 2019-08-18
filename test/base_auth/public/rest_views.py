from django.contrib.auth import logout as django_logout
from django.utils.translation import ugettext_lazy as _

from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from base_auth.web.serializers import UserSerializer
from system.utils.logset import add_operate_log
from system.utils import module


@api_view(['GET', 'POST'])
@permission_classes((permissions.AllowAny,))
def logout(request):
    user = request.user
    add_operate_log(user, module.BASE_AUTH_MODULE_ID,
                    'name[{}] logout system, user name [{}]'.format(user.username, user.name or user.username), 0,
                    _('x_system_logout').format(user.name or user.username), )
    django_logout(request)
    return Response(status=status.HTTP_200_OK)


@api_view(['GET', ])
@permission_classes((permissions.IsAuthenticated,))
def user_info(request):
    user = request.user
    data = UserSerializer(user).data
    return Response(data=data, status=status.HTTP_200_OK)
