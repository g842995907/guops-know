from django.templatetags.static import static

DEDAULT_USER_LOGO = static('x_person/img/user_default.jpg')

DEDAULT_TEAM_LOGO = static('x_person/img/team_logo.png')

DEDAULT_EVENT_LOGO_TEMPLATE = lambda sub_app_name: static('event_%s/web/img/default_cover.png' % sub_app_name)