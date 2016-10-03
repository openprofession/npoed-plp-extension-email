# coding: utf-8

import base64
from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.views.generic import CreateView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from api.views.user import ApiKeyPermission
from plp.models import User
from .forms import BulkEmailForm
from .models import BulkEmailOptout
from .notifications import BulkEmailSend
from .utils import filter_users


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
        self.object.target = form.to_json()
        self.object.save()
        msgs = BulkEmailSend(self.object)
        msgs.send()
        return JsonResponse({'redirect_url': self.get_success_url()})

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        form_html = get_template('extension_email/_message_form.html').render(context={'form': form}, request=request)
        if form.is_valid():
            if '_check_users_count' in request.POST:
                return JsonResponse({
                    'user_count': filter_users(form.to_json()).count(),
                    'theme': form.cleaned_data['subject'],
                    'form': form_html,
                    'valid': True,
                })
            return self.form_valid(form)
        else:
            return JsonResponse({'form': form_html, 'valid': False})


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


class OptoutStatusView(APIView):
    """
        **Описание**

            Ручка для проверки и изменения статуса подписки пользователя на информационные
            рассылки платформы. Требуется заголовок X-PLP-Api-Key.

        **Пример запроса**

            GET bulk_email/api/optout_status/?user=<username>

            POST bulk_email/api/optout_status/{
                "user" : username,
                 "status" : boolean
            }

        **Параметры post-запроса**

            * user: логин пользователя
            * status: True/False для активации/деактивации подписки соответственно

        **Пример ответа**

            * {
                  "status": True
              }

            новый статус подписки

            404 если пользователь не найден
            400 если переданы не все параметры

    """
    permission_classes = (ApiKeyPermission,)

    def get(self, request, *args, **kwargs):
        username = request.query_params.get('user')
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        optout = BulkEmailOptout.objects.filter(user=user).first()
        if optout:
            return Response({'status': False})
        else:
            return Response({'status': True})

    def post(self, request, *args, **kwargs):
        username = request.data.get('user')
        new_status = request.data.get('status')
        if isinstance(new_status, basestring):
            new_status = new_status.lower() != 'false'
        if not username or new_status is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        old_status = not BulkEmailOptout.objects.filter(user=user).exists()
        if new_status == old_status:
            return Response({'status': new_status})
        if new_status:
            BulkEmailOptout.objects.filter(user=user).delete()
        else:
            BulkEmailOptout.objects.create(user=user)
        return Response({'status': new_status})
