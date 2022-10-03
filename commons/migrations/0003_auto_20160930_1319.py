# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0002_auto_20160909_1217'),
    ]

    operations = [
        migrations.AddField(
            model_name='learningpath',
            name='original_language',
            field=models.CharField(default=b'', max_length=5, verbose_name='original language code', db_index=True),
        ),
        migrations.AddField(
            model_name='oer',
            name='original_language',
            field=models.CharField(default=b'', max_length=5, verbose_name='original language code', db_index=True),
        ),
        migrations.AddField(
            model_name='project',
            name='original_language',
            field=models.CharField(default=b'', max_length=5, verbose_name='original language code', db_index=True),
        ),
        migrations.AddField(
            model_name='repo',
            name='original_language',
            field=models.CharField(default=b'', max_length=5, verbose_name='original language code', db_index=True),
        ),
    ]
