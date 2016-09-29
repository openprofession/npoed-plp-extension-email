# coding: utf-8

from django.http import HttpResponse, Http404


def from_support_view(request):
    if not request.user.is_superuser:
        raise Http404
    return HttpResponse()

