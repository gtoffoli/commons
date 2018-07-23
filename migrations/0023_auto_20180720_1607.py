# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0022_auto_20180702_1218'),
    ]

    operations = [
        migrations.AddField(
            model_name='folder',
            name='description',
            field=models.TextField(null=True, verbose_name='short description', blank=True),
        ),
        migrations.AddField(
            model_name='folder',
            name='slug',
            field=django_extensions.db.fields.AutoSlugField(editable=False, populate_from='get_title', max_length=80, blank=True, overwrite=True),
        ),
        migrations.AddField(
            model_name='folderdocument',
            name='description',
            field=models.TextField(null=True, verbose_name='short description', blank=True),
        ),
        migrations.AddField(
            model_name='folderdocument',
            name='slug',
            field=django_extensions.db.fields.AutoSlugField(editable=False, populate_from='__str__', max_length=80, blank=True, overwrite=True),
        ),
    ]
