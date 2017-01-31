# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0011_auto_20170130_1454'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectmember',
            name='refused',
            field=models.DateTimeField(default=None, null=True, verbose_name='last refusal'),
        ),
    ]
