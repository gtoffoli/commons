# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0009_auto_20161219_1351'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='mentoring_model',
            field=models.PositiveIntegerField(default=1, help_text='once mentoring projects exist, you can only move from model A or B to A+B.', null=True, verbose_name='mentoring model', choices=[(0, 'no mentoring'), (1, 'A - Administrator chooses mentor'), (2, 'B - Mentee chooses mentor'), (3, 'A+B - Administrator or mentee chooses mentor')]),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='mentor_for_all',
            field=models.BooleanField(default=False, help_text='available to act as mentor also for member of other communities.', verbose_name='available as mentor for other communities'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='mentor_unavailable',
            field=models.BooleanField(default=False, help_text='temporarily unavailable to accept (more) requests by mentees.', verbose_name='currently not available as mentor'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='p2p_communication',
            field=models.TextField(verbose_name='P2P communication preferences', blank=True),
        ),
        migrations.AlterField(
            model_name='projectmember',
            name='state',
            field=models.IntegerField(default=0, null=True, verbose_name=b'membership state', choices=[(0, 'request submitted'), (1, 'request accepted'), (2, 'request rejected'), (3, 'membership suspended or expired')]),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='curriculum',
            field=models.ForeignKey(related_name='profile_curriculum', verbose_name='curriculum', blank=True, to='commons.Document', null=True),
        ),
    ]
