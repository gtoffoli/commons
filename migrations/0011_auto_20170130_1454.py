# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0010_auto_20170116_1430'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='mentoring_model',
            field=models.PositiveIntegerField(help_text='once mentoring projects exist, you can only move from model A or B to A+B.', null=True, verbose_name='mentoring model', choices=[(0, 'no mentoring'), (1, 'A - Administrator chooses mentor'), (2, 'B - Mentee chooses mentor'), (3, 'A+B - Administrator or mentee chooses mentor')]),
        ),
    ]
