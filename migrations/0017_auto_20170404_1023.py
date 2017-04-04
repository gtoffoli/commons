# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0016_auto_20170223_1149'),
    ]

    operations = [
        migrations.AddField(
            model_name='oer',
            name='content',
            field=models.TextField(help_text='formal description of a problem or other original content', null=True, verbose_name='content', blank=True),
        ),
        migrations.AddField(
            model_name='project',
            name='allow_external_mentors',
            field=models.BooleanField(default=False, verbose_name='allow external mentors'),
        ),
        migrations.AlterField(
            model_name='project',
            name='mentoring_model',
            field=models.PositiveIntegerField(help_text='once mentoring projects exist, you can only move from model A or B to A+B.', null=True, verbose_name='mentoring setup model', choices=[(0, 'mentoring is not available'), (1, 'A - The community administrator chooses the mentor'), (2, 'B - The mentee chooses the mentor'), (3, 'B+A - The mentee or the administrator choose the mentor')]),
        ),
    ]
