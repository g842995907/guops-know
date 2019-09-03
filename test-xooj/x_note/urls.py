from django.conf.urls import url, include

from x_note import views

urlpatterns = [
    url(r'^mynote/$', views.NoteView.as_view(), name='mynote'),
    url(r'^save_note/$', views.save_note, name='save_note')
]
