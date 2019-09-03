from base.utils.app import load_app_settings
from base.utils.rest.patch import monkey_patch


app_settings = load_app_settings(__package__)


def sync_init():
    monkey_patch()
