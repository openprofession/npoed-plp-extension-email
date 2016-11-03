# coding: utf-8

import json
from django.utils import timezone
from plp.models import User, EnrollmentReason, Participant
from .forms import BulkEmailForm, CustomUnicodeCourseSession


def filter_users(support_email):
    """
    Фильтрация пользователей по данным модели массовой рассылки.
    Возвращает queryset пользователей и тип фильтра ('to_all', 'to_myself' или '')
    """
    def _check_enrollment_type_chosen():
        return data['enrollment_type'] != BulkEmailForm.ENROLLMENT_TYPE_INITIAL

    def _check_get_certificate_chosen():
        return len(data['got_certificate'])

    data = support_email.target
    if data.get('to_myself'):
        return User.objects.filter(username=support_email.sender.username), 'to_myself'
    dic = {'bulk_email_optout__isnull': True}
    dic_exclude = {}
    session_ids = []
    to_all = True
    # если фильтр по сессиям будет нужен, но пользователь не выбрал ни одной сессии
    if not data['session_filter'] and (_check_enrollment_type_chosen() or _check_get_certificate_chosen()):
        data['session_filter'] = CustomUnicodeCourseSession.get_ordered_queryset()
    if data['session_filter']:
        to_all = False
        session_ids = data['session_filter']
        dic.update({'participant__session__id__in': session_ids})
    last_login_from = data.get('last_login_from') or BulkEmailForm.MIN_DATE
    last_login_to = data.get('last_login_to') or BulkEmailForm.MAX_DATE
    register_date_from = data.get('register_date_from') or BulkEmailForm.MIN_DATE
    register_date_to = data.get('register_date_to') or BulkEmailForm.MAX_DATE
    if last_login_from != BulkEmailForm.MIN_DATE or last_login_to != BulkEmailForm.MAX_DATE:
        to_all = False
        dic.update({
            'last_login__gte': timezone.datetime.strptime(last_login_from, BulkEmailForm.DATETIME_FORMAT),
            'last_login__lte': timezone.datetime.strptime(last_login_to, BulkEmailForm.DATETIME_FORMAT) + timezone.timedelta(1,0,0),
        })
    if register_date_from != BulkEmailForm.MIN_DATE or register_date_to != BulkEmailForm.MAX_DATE:
        to_all = False
        dic.update({
            'date_joined__gte': timezone.datetime.strptime(register_date_from, BulkEmailForm.DATETIME_FORMAT),
            'date_joined__lte': timezone.datetime.strptime(register_date_to, BulkEmailForm.DATETIME_FORMAT) + timezone.timedelta(1,0,0),
        })

    # выбран ли конкретный платный/бесплатный вариант прохождения или тип сертификата
    # для фильтрации по EnrollmentReason
    paid = None
    if _check_enrollment_type_chosen():
        to_all = False
        if 'paid' in data['enrollment_type']:
            paid = True
        elif 'free' in data['enrollment_type']:
            paid = False
    elif len(data['got_certificate']) == 1:
        if 'paid' in data['got_certificate']:
            paid = True
        elif 'free' in data['got_certificate']:
            paid = False

    if paid is not None:
        paid_enr = list(EnrollmentReason.objects.filter(
            participant__session__id__in=session_ids,
            session_enrollment_type__mode='verified'
        ).values_list('participant__user__id', flat=True).distinct())
        if paid:
            dic.update({'id__in': paid_enr})
        else:
            dic_exclude.update({'id__in': paid_enr})
    if data['got_certificate']:
        # если не совпадает тип прохождения и платность полученного сертификата
        if len(data['enrollment_type']) == 1 and len(data['got_certificate']) == 1 and \
                data['enrollment_type'] != data['got_certificate']:
            return User.objects.none(), ''
        to_all = False
        have_cert = list(Participant.objects.filter(
            is_graduate=data.get('passed', False),
            session__id__in=session_ids,
        ).values_list('user__id', flat=True))
        if 'id__in' in dic:
            dic['id__in'] = set(dic['id__in']).intersection(set(have_cert))
        else:
            dic['id__in'] = have_cert

    if 'id__in' in dic:
        dic.pop('participant__session__id__in', None)
    # т.к. все пользователи в plp пушатся активными, проверяем реальную активность в sso так
    users = User.objects.filter(**dic).exclude(**dic_exclude).exclude(last_name='').distinct()
    return users, 'to_all' if to_all else ''
