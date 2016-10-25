# coding: utf-8

import logging
from django.utils.timezone import now
from celery import task
from .notifications import BulkEmailSend


@task
def support_mass_send(obj):
    logging.info('%s Started sending bulk emails' % now().strftime('%H:%M:%S %d.%m.%Y'))
    msgs = BulkEmailSend(obj)
    msgs.send()
    logging.info('%s Ended sending bulk emails' % now().strftime('%H:%M:%S %d.%m.%Y'))
