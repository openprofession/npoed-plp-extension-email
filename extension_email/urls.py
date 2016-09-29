# coding: utf-8

from django.conf.urls import url
from extension_email import views


urlpatterns = [
    url(r'^from_support/?$', views.from_support_view, name='from-support')
]

