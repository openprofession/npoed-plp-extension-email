# coding: utf-8

from django.conf.urls import url
from extension_email import views


urlpatterns = [
    url(r'^from_support/?$', views.FromSupportView.as_view(), name='from-support'),
    url(r'^unsubscribe/(?P<hash_str>.+)/?', views.unsubscribe, name='bulk-unsubscribe'),
]

