from django.conf.urls import url

from common_cms import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^upload_logo/$', views.upload_logo, name='upload_logo'),
    url(r'^upload_image/$', views.upload_image, name='common_upload_image'),
    url(r'^remove_image/$', views.remove_image, name='common_remove_image'),

    url(r'^upload_markdown/$', views.upload_markdown, name='common_upload_markdown'),

    url(r'^validate_example/$', views.validate_example, name='validate_example'),
]
