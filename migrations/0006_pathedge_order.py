# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0005_auto_20161110_1623'),
    ]

    operations = [
        migrations.AddField(
            model_name='pathedge',
            name='order',
            field=models.IntegerField(default=0),
        ),
    ]
