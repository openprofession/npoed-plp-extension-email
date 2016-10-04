# coding: utf-8

from datetime import date
from django import forms
from django.db.models import Case, When, Value, QuerySet
from django.db.models.fields import BooleanField
from django.contrib.admin.widgets import FilteredSelectMultiple, AdminDateWidget
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from plp.models import CourseSession
from .models import SupportEmail


class CustomUnicodeCourseSession(CourseSession):
    class Meta:
        proxy = True
        ordering = []

    def __unicode__(self):
        now = timezone.now()
        d = {
            'univ': self.course.university.abbr,
            'course': self.course.title,
            'session': self.slug,
        }
        if self.datetime_starts and self.datetime_ends and self.datetime_starts < now < self.datetime_ends:
            week = (timezone.now().date() - self.datetime_starts.date()).days / 7 + 1
            return u'{univ} - {course} - {session} (неделя {week})'.format(week=week, **d)
        elif self.datetime_starts and self.datetime_starts > now:
            return u'{univ} - {course} - {session} (старт {date})'.format(date=now.strftime('%d.%m.%Y'), **d)
        else:
            return u'{univ} - {course} - {session}'.format(**d)

    @staticmethod
    def get_ordered_queryset():
        now = timezone.now()
        return CustomUnicodeCourseSession.objects.annotate(
            current=Case(
                When(datetime_starts__lt=now, datetime_ends__gt=now, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            ),
            future=Case(
                When(datetime_starts__gt=now, then=Value(True)),
                default=False,
                output_field=BooleanField()
            )
        ).order_by('-current', '-future', '-datetime_starts')


class BulkEmailForm(forms.ModelForm):
    DATETIME_FORMAT = '%d.%m.%Y'
    MIN_DATE = '01.01.2000'
    MAX_DATE = '01.01.2030'
    ENROLLMENT_TYPE_INITIAL = ['paid', 'free']

    session_filter = forms.ModelMultipleChoiceField(
        queryset=CustomUnicodeCourseSession.get_ordered_queryset(),
        widget=FilteredSelectMultiple(verbose_name=_(u'Сессии'),
                                      is_stacked=False,
                                      attrs={'style': 'min-height: 270px'}),
        required=False,
        label=_(u'Сессия курса')
    )
    last_login_from = forms.DateField(label=_(u'Дата последнего входа от'), widget=AdminDateWidget(),
                                      input_formats=[DATETIME_FORMAT], initial=MIN_DATE)
    last_login_to = forms.DateField(label=_(u'Дата последнего входа до'), widget=AdminDateWidget(),
                                    input_formats=[DATETIME_FORMAT], initial=MAX_DATE)
    register_date_from = forms.DateField(label=_(u'Дата регистрации от'), widget=AdminDateWidget(),
                                         input_formats=[DATETIME_FORMAT], initial=MIN_DATE)
    register_date_to = forms.DateField(label=_(u'Дата регистрации до'), widget=AdminDateWidget(),
                                       input_formats=[DATETIME_FORMAT], initial=MAX_DATE)
    enrollment_type = forms.MultipleChoiceField(choices=(
        ('paid', _(u'Платники')),
        ('free', _(u'Бесплатники'))
    ), widget=forms.CheckboxSelectMultiple, label=_(u'Тип записи'), initial=ENROLLMENT_TYPE_INITIAL)
    got_certificate = forms.MultipleChoiceField(choices=(
        ('paid', _(u'Пользователь получил платный сертификат')),
        ('free', _(u'Пользователь получил бесплатный сертификат')),
    ), widget=forms.CheckboxSelectMultiple, label=_(u'Получен сертификат'), required=False,
       help_text=_(u'Если не выбран ни один из чекбоксов - рассылка для всех пользователей, которые и получили, '
                   u'и не получили сертификаты. Если выбран один чекбокс - то только пользователям платникам либо '
                   u'бесплатникам, получившим сертификат. Если оба - то всем пользователям, получившим сертификат'))

    def __init__(self, *args, **kwargs):
        super(BulkEmailForm, self).__init__(*args, **kwargs)
        self.fields['subject'].required = True
        self.fields['text_message'].required = True

    def to_json(self):
        data = getattr(self, 'cleaned_data', {})
        result = {}
        for k, v in data.iteritems():
            if k in self.Meta.fields:
                continue
            if isinstance(v, date):
                result[k] = v.strftime(self.DATETIME_FORMAT)
            elif isinstance(v, QuerySet):
                result[k] = [int(i.pk) for i in v]
            else:
                result[k] = v
        return result

    class Meta:
        model = SupportEmail
        fields = ['subject', 'text_message']
        widgets = {
            'subject': forms.TextInput(attrs={'style': 'width: 100%'}),
            'text_message': forms.Textarea(attrs={'style': 'width: 100%'}),
        }
        help_texts = {
            'text_message': _(u'Можно использовать переменные {{ user.get_full_name }} для подстановки '
                              u'имени и фамилии пользователя в текст, {{ user.first_name }} - имени, '
                              u'{{ user.last_name }} - фамилии, {{ user.email }} - email')
        }

    class Media:
        css = {'all': ['admin/css/widgets.css']}
        js = ['/admin/jsi18n/']
