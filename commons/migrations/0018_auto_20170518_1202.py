# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0017_auto_20170404_1023'),
    ]

    operations = [
        migrations.AddField(
            model_name='folderdocument',
            name='embed_code',
            field=models.TextField(null=True, verbose_name='embed code', blank=True),
        ),
        migrations.AlterField(
            model_name='folderdocument',
            name='document',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='folderdocument_document', verbose_name='document', blank=True, to='commons.Document', null=True),
        ),
        migrations.AlterField(
            model_name='oerevaluation',
            name='user',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='oer_evaluator', verbose_name='evaluator', to=settings.AUTH_USER_MODEL),
        ),
    ]
