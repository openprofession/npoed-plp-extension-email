# coding: utf-8

from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect, Http404
from django.views.generic import CreateView
from .forms import BulkEmailForm
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
