from django.conf.urls import url, include

from common_web import views

urlpatterns = [
    url(r'^$', views.home, name='index'),
    url(r'^login/$', views.login, name='login'),
    url(r'^register/$', views.register, name='register'),
    url(r'^handlerlogin/$', views.handlerlogin, name='handlerlogin'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^home/$', views.home, name='home'),
    url(r'^person/$', views.index, name='person'),
    url(r'^403/$', views.forbidden, name='forbidden'),
    url(r'^404/$', views.not_found, name='not_found'),
    url(r'^500/$', views.server_error, name='server_error'),
    url(r'^cloud/', include("common_cloud.urls", namespace='cloud')),
    url(r'^note/', include("x_note.urls", namespace='note')),
    url(r'^authorization/$', views.authorization, name='authorization'),
    # url(r'^forget_password/$', views.forget_password, name='forget_password'),
    url(r'^set_password/', views.set_password, name='set_password'),
    url(r'^license_upload/$', views.license_upload, name='license_upload'),
    url(r'^submit_register/$', views.submit_register, name='submit_register'),
    url(r'^report_online/$', views.report_online, name='report_online'),
    url(r'^message/$', views.message, name='message'),
]
