# coding: utf-8

import base64
from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
from django.views.generic import CreateView
from plp.models import User
from .forms import BulkEmailForm
from .models import BulkEmailOptout
from .notifications import BulkEmailSend


class FromSupportView(CreateView):
    form_class = BulkEmailForm
    success_url = reverse_lazy('frontpage')
    template_name = 'extension_email/main.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return super(FromSupportView, self).dispatch(request, *args, **kwargs)
        raise Http404

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.sender = self.request.user
        self.object.save()
        msgs = BulkEmailSend(self.object)
        msgs.send()
        return HttpResponseRedirect(self.get_success_url())


def unsubscribe(request, hash_str):
    try:
        s = base64.b64decode(hash_str)
    except TypeError:
        raise Http404
    try:
        user = User.objects.get(username=s)
    except User.DoesNotExist:
        raise Http404
    BulkEmailOptout.objects.get_or_create(user=user)
    context = {
        'profile_url': '{}/profile/'.format(settings.SSO_NPOED_URL),
    }
    return render(request, 'extension_email/unsubscribed.html', context)

