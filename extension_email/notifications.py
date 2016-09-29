# coding: utf-8

from plp.notifications.base import MassSendEmails


class BulkEmailSend(MassSendEmails):
    def __init__(self, obj):
        self.obj = obj
        super(BulkEmailSend, self).__init__()

    def get_emails(self):
        return [i.email for i in self.obj.get_recipients()]

    def get_subject(self, email=None):
        return self.obj.subject

    def get_text(self, email=None):
        return self.obj.text_message

    def get_html(self, email=None):
        return self.obj.html_message

    def get_context(self, email=None):
        return {}
