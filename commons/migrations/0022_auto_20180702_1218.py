# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0021_auto_20180625_1059'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='chat_type',
        ),
        migrations.AlterField(
            model_name='document',
            name='language',
            field=models.CharField(default='en', max_length=8, verbose_name='Language', choices=[('en', 'English'), ('it', 'Italiano'), ('pt', 'Portugu\xeas')]),
        ),
    ]
