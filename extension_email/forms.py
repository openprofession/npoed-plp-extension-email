# coding: utf-8

from django import forms
from .models import SupportEmail


class BulkEmailForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BulkEmailForm, self).__init__(*args, **kwargs)
        self.fields['subject'].required = True
        self.fields['text_message'].required = True

    class Meta:
        model = SupportEmail
        fields = ['target', 'subject', 'text_message']
        widgets = {
            'target': forms.RadioSelect(),
        }
