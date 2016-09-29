# coding: utf-8

from django.contrib import admin
from autocomplete_light import modelform_factory
from .models import SupportEmail


@admin.register(SupportEmail)
class SupportEmailAdmin(admin.ModelAdmin):
    list_display = ('sender', 'subject', 'target', 'created')
    form = modelform_factory(SupportEmail, exclude=[])
