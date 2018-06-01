# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('extension_email', '0004_supportemailtemplate'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CustomUnicodeCourseSession',
        ),
    ]
