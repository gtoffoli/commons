# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0025_auto_20180720_1746'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='mentoring_available',
            field=models.BooleanField(default=False, verbose_name='mentoring is available'),
        ),
        migrations.AlterField(
            model_name='metadatatype',
            name='validation',
            field=models.CharField(blank=True, max_length=64, verbose_name='Validation function name', choices=[('Parse date', 'Parse date'), ('Parse date and time', 'Parse date and time'), ('Parse time', 'Parse time')]),
        ),
        migrations.AlterField(
            model_name='oer',
            name='project',
            field=models.ForeignKey(related_name='oer_project', on_delete=django.db.models.deletion.PROTECT, blank=True, to='commons.Project', help_text='where the OER has been cataloged or created', null=True),
        ),
        migrations.AlterField(
            model_name='pathnode',
            name='children',
            field=models.ManyToManyField(related_name='_parents', null=True, through='commons.PathEdge', to='commons.PathNode', blank=True),
        ),
    ]
