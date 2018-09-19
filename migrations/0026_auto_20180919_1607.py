# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0025_auto_20180720_1746'),
    ]

    operations = [
        migrations.AlterField(
            model_name='metadatatype',
            name='validation',
            field=models.CharField(blank=True, max_length=64, verbose_name='Validation function name', choices=[('Parse date', 'Parse date'), ('Parse date and time', 'Parse date and time'), ('Parse time', 'Parse time')]),
        ),
        migrations.AlterField(
            model_name='pathnode',
            name='children',
            field=models.ManyToManyField(related_name='_parents', null=True, through='commons.PathEdge', to='commons.PathNode', blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='mentoring_model',
            field=models.PositiveIntegerField(blank=True, help_text='once mentoring projects exist, you can only move from model A or B to A+B.', null=True, verbose_name='mentoring setup model', choices=[(0, 'mentoring is not available'), (1, 'A - The community administrator chooses the mentor'), (2, 'B - The mentee chooses the mentor'), (3, 'B+A - The mentee or the administrator choose the mentor')]),
        ),
    ]
