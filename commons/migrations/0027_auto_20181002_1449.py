# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0026_auto_20181002_1047'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='mentoring_model',
            field=models.PositiveIntegerField(blank=True, help_text='once mentoring projects exist, you can only move from model A or B to A+B.', null=True, verbose_name='mentoring setup model', choices=[(0, 'mentoring is not available'), (1, 'A - The community administrator chooses the mentor'), (2, 'B - The mentee chooses the mentor'), (3, 'B+A - The mentee or the administrator choose the mentor')]),
        ),
    ]
