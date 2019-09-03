from functools import partial

from django.contrib.auth.decorators import login_required as django_login_required

login_required = partial(django_login_required, login_url='common_web:login')