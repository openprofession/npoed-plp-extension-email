# coding: utf-8

from django.db import models
from django.utils.translation import ugettext_lazy as _
from plp.models import User


class SupportEmail(models.Model):
    TARGET_CHOICES = (
        ('myself', _(u'Себе')),
        ('everyone', _(u'Всем')),
    )

    sender = models.ForeignKey(User, verbose_name=_(u'Отправитель'))
    target = models.CharField(max_length=15, choices=TARGET_CHOICES, verbose_name=_(u'Фильтр'), default='myself')
    subject = models.CharField(max_length=128, blank=True, verbose_name=_(u'Тема'))
    html_message = models.TextField(null=True, blank=True, verbose_name=_(u'HTML письма'))
    text_message = models.TextField(null=True, blank=True, verbose_name=_(u'Текст письма'))
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _(u'Рассылка')
        verbose_name_plural = _(u'Рассылки')

    def __unicode__(self):
        return '%s - %s' % (self.sender, self.subject)

    def get_recipients(self):
        if self.target == 'myself':
            return [self.sender]
        elif self.target == 'everyone':
            return User.objects.filter(bulk_email_optout__isnull=True)


class BulkEmailOptout(models.Model):
    user = models.ForeignKey(User, verbose_name=_(u'Пользователь'), related_name='bulk_email_optout')
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name=_(u'Когда пользователь отписался от рассылки'))

    class Meta:
        verbose_name = _(u'Отписка от рассылок')
        verbose_name_plural = _(u'Отписки от рассылок')
