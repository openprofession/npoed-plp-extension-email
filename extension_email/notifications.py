# coding: utf-8

import base64
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from plp.notifications.base import MassSendEmails


class BulkEmailSend(MassSendEmails):
    def __init__(self, obj):
        self.obj = obj
        self.email_to_user = {}
        super(BulkEmailSend, self).__init__()

    def get_emails(self):
        recipients = self.obj.get_recipients()
        self.email_to_user = dict([(i.email, i) for i in recipients])
        return self.email_to_user.keys()

    def get_subject(self, email=None):
        return self.obj.subject

    def get_text(self, email=None):
        return self.add_unsubscribe_footer(email, plaintext_msg=self.obj.text_message)

    def get_html(self, email=None):
        return self.add_unsubscribe_footer(email, html_msg=self.obj.html_message)

    def get_context(self, email=None):
        return {}

    def get_extra_headers(self, email=None):
        return {'List-Unsubscribe': self.get_unsubscribe_url(email)}

    def get_unsubscribe_url(self, email):
        username = self.email_to_user.get(email).username
        url = reverse('bulk-unsubscribe', kwargs={'hash_str': base64.b64encode(username)})
        return '{prefix}://{site}{url}'.format(url=url, **self.defaults)

    def add_unsubscribe_footer(self, email, plaintext_msg=None, html_msg=None):
        url = self.get_unsubscribe_url(email)
        if plaintext_msg:
            return _(u'{0}\n\nДля отписки от информационной рассылки команды платформы {1} перейдите '
                     u'по ссылке {2}'.format(plaintext_msg, self.defaults['PLATFORM_NAME'], url))
        if html_msg:
            return _(u'{0}<br/><p>Для отписки от информационной рассылки команды платформы {1} перейдите '
                     u'<a href="{2}">по ссылке</a></p>'.format(html_msg, self.defaults['PLATFORM_NAME'], url))
        return ''
