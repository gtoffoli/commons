# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0018_auto_20170518_1202'),
    ]

    operations = [
        migrations.AddField(
            model_name='folderdocument',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(default=None, verbose_name='created', null=True, editable=False, blank=True),
        ),
    ]
