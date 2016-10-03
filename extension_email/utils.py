# coding: utf-8

import json
from django.utils import timezone
from plp.models import User, EnrollmentReason, Participant
from .forms import BulkEmailForm


def filter_users(data):
    """
    Фильтрация пользователей по данным формы массовой рассылки
    """
    dic = {'bulk_email_optout__isnull': True}
    session_ids = []
    if data['session_filter']:
        session_ids = data['session_filter']
        dic.update({'participant__session__id__in': session_ids})
    last_login_from = data.get('last_login_from') or BulkEmailForm.MIN_DATE
    last_login_to = data.get('last_login_to') or BulkEmailForm.MAX_DATE
    register_date_from = data.get('register_date_from') or BulkEmailForm.MIN_DATE
    register_date_to = data.get('register_date_to') or BulkEmailForm.MAX_DATE
    if last_login_from != BulkEmailForm.MIN_DATE or last_login_to != BulkEmailForm.MAX_DATE:
        dic.update({
            'last_login__gte': timezone.datetime.strptime(last_login_from, BulkEmailForm.DATETIME_FORMAT),
            'last_login__lte': timezone.datetime.strptime(last_login_to, BulkEmailForm.DATETIME_FORMAT),
        })
    if register_date_from != BulkEmailForm.MIN_DATE or register_date_to != BulkEmailForm.MAX_DATE:
        dic.update({
            'date_joined__gte': timezone.datetime.strptime(register_date_from, BulkEmailForm.DATETIME_FORMAT),
            'date_joined__lte': timezone.datetime.strptime(register_date_to, BulkEmailForm.DATETIME_FORMAT),
        })
    users = User.objects.filter(**dic)
    paid = None
    if data['enrollment_type'] != BulkEmailForm.ENROLLMENT_TYPE_INITIAL or len(data['got_certificate']) == 1:
        if 'paid' in data['enrollment_type'] and 'paid' in data['got_certificate']:
            paid = True
        elif 'free' in data['enrollment_type'] and 'free' in data['got_certificate']:
            paid = False
        else:
            # если выбор типа записи не соответствует выбору типа сертификата
            return User.objects.none()
    if paid is not None:
        paid_enr = EnrollmentReason.objects.filter(
            participant__session__id__in=session_ids,
            participant__user__in=users,
            session_enrollment_type__mode='verified'
        ).values_list('participant__user__id', flat=True)
        if paid:
            users = users.filter(id__in=paid_enr)
        else:
            users = users.exclude(id__in=paid_enr)
    if data['got_certificate']:
        have_cert = []
        participants = Participant.objects.filter(
            session__id__in=session_ids, user__in=users
        ).values_list('user__id', 'certificate_data')
        for user_id, cert_data in participants:
            try:
                data = json.loads(cert_data)
            except (ValueError, TypeError):
                data = {}
            if data.get('passed', False):
                have_cert.append(user_id)
        users = users.filter(id__in=have_cert)
    return users.distinct()
