# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0013_auto_20170215_1312'),
    ]

    operations = [
        migrations.AlterField(
            model_name='folder',
            name='title',
            field=models.CharField(max_length=128, verbose_name='Title'),
        ),
        migrations.AlterField(
            model_name='project',
            name='mentoring_model',
            field=models.PositiveIntegerField(help_text='once mentoring projects exist, you can only move from model A or B to A+B.', null=True, verbose_name='mentoring setup model', choices=[(0, 'no mentoring'), (1, 'A - Administrator chooses mentor'), (2, 'B - Mentee chooses mentor'), (3, 'B+A - Mentee chooses mentor or administrator')]),
        ),
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(max_length=78, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='project',
            name='slug',
            field=django_extensions.db.fields.AutoSlugField(editable=False, populate_from='name', blank=True, unique=True, overwrite=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='mentor_for_all',
            field=models.BooleanField(default=False, help_text='available to act as mentor also for members of other communities.', verbose_name='available as mentor for other communities'),
        ),
    ]
