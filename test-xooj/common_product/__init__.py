# -*- coding: utf-8 -*-
import logging
import products

logger = logging.getLogger(__name__)
__version__ = '1.1.1'

# XCTF_APPS = []
#
# for app in products.ALL_PRODUCT:
#     try:
#         __import__(app)
#         XCTF_APPS.append(app)
#     except Exception, e:
#         logging.info("%s app not exist", app)
#
#
# BASE_APPS = []
# for app in products.BASE_APP:
#     try:
#         __import__(app)
#         BASE_APPS.append(app)
#     except Exception:
#         logging.info("%s common app not exist", app)