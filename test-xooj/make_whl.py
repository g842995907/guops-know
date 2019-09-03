import fileinput
import os
import shutil

from common_product import products_all
from common_product import products
def make(app):
    shutil.copy('setup_templet.py', 'setup.py')
    for line in fileinput.input('setup.py', inplace=1):
        line = line.replace('templet_app_name', app)
        print line

    os.system("python setup.py bdist_wheel")

    os.system("rm -rf *.egg-info")
    os.system("rm -rf build")

for app in products.BASE_APP:
    make(app)

for app in products_all.ALL_PRODUCT:
    make(app)


