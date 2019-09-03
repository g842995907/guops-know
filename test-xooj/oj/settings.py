# -*- coding: utf-8 -*-
import os
import sys

reload(sys)
sys.setdefaultencoding('utf8')

from django.utils.translation import ugettext_lazy as _

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '(r*2px6n-_8t+&g#w=v-k#vs1@7%g6c7l@1aqy*d%*$_4$^-(c'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'x_i18n',
    'channels',
    'channels.delay',
    'django_extensions',
]

import common_product.products as product

BASE_APPS = product.BASE_APP

for app in BASE_APPS:
    INSTALLED_APPS.append(app)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    #'django.contrib.sessions.middleware.SessionMiddleware',
    'common_framework.middleware.session_middleware.XSessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # 'django.contrib.auth.middleware.AuthenticationMiddleware',
    'cached_auth.Middleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'common_framework.middleware.license_middleware.LicenseMiddleware',
    'common_framework.middleware.request_middleware.ProcessRequestsMiddleware',
]
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(levelname)s %(asctime)s %(module)s - %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'logfile': {
            'class': 'cloghandler.ConcurrentRotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'log/oj.log'),
            'formatter': 'standard',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 10,
        },
        'mail_admin': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': False,
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admin'],
            'propagate': True,
            'level': 'ERROR',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'logfile']
    },
}

# example: ADMINS = (('nick', 'xxx@xxx.xx'),)
ADMINS = ()

ROOT_URLCONF = 'oj.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'oj.wsgi.application'


from oj.config import *
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_L10N = True
USE_TZ = False
LANGUAGES = [
    ('zh-hans', _('Chinese')),
    ('en', _('English')),
]

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

PLATFORM_TYPE = "ALL"
if PLATFORM_TYPE == "AD":
    from common_product import products_ad
    XCTF_APPS = products_ad.ALL_PRODUCT
elif PLATFORM_TYPE == "OJ":
    from common_product import products_oj
    XCTF_APPS = products_oj.ALL_PRODUCT
else:
    from common_product import products_all
    XCTF_APPS = products_all.ALL_PRODUCT


for app in XCTF_APPS:
    INSTALLED_APPS.append(app)

STATIC_V_DIRS = [os.path.join(BASE_DIR, app_name) for app_name in BASE_APPS + XCTF_APPS]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),

    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),

    'EXCEPTION_HANDLER': 'common_framework.views.exception_handler',

    # Input and output formats (关闭时区设置以下)
    'DATE_FORMAT': '%Y-%m-%d',
    'DATE_INPUT_FORMATS': ('%Y-%m-%d',),

    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATETIME_INPUT_FORMATS': ('%Y-%m-%d %H:%M:%S',),

    'TIME_FORMAT': '%H:%M:%S',
    'TIME_INPUT_FORMATS': ('%H:%M:%S',),
}
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

BACKUP_ROOT = './backup'
BACKUP_DIRS = ['course/pdf', ]

# Session
SESSION_COOKIE_NAME = 'oj_sessionid'
SESSION_COOKIE_AGE = 60 * 60 * 24
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_ENGINE = 'common_framework.utils.x_sessionStore'
CSRF_COOKIE_NAME = 'oj_csrftoken'


AUTH_USER_MODEL = 'common_auth.User'
ADMIN_SLUG = 'admin'

DEFAULT_CACHE_AGE = 300
CACHES = {
    'memcache': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'KEY_PREFIX': 'XOJ',
    },
    'default': {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        # "LOCATION": "redis://:{}@127.0.0.1:6379/1".format(REDIS_PASS),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}


CRONTAB_COMMAND_PREFIX = 'export JAVA_HOME=/usr/lib/jvm/java;'
CRONJOBS = []

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "asgi_redis.RedisChannelLayer",
        "CONFIG": {
            "hosts": ["redis://127.0.0.1:6379/0"],
            # "hosts": ["redis://:{}@127.0.0.1:6379/0".format(REDIS_PASS)],
            "prefix": u"ad",
            "expiry": 60 * 10,
            "capacity": 8192,
        },
        "ROUTING": "oj.routing.channel_routing",
    },
}
