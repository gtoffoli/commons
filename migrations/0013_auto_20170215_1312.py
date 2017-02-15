# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import awesome_avatar.fields


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0012_projectmember_refused'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='prototype',
            field=models.ForeignKey(related_name='prototype_project', verbose_name='prototypical Learning Path', blank=True, to='commons.LearningPath', null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='big_image',
            field=awesome_avatar.fields.AvatarField(upload_to=b'images/projects/', null=True, verbose_name='featured image', blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='mentoring_model',
            field=models.PositiveIntegerField(help_text='once mentoring projects exist, you can only move from model A or B to A+B.', null=True, verbose_name='mentoring model', choices=[(0, 'no mentoring'), (1, 'A - Administrator chooses mentor'), (2, 'B - Mentee chooses mentor')]),
        ),
        migrations.AlterField(
            model_name='project',
            name='small_image',
            field=awesome_avatar.fields.AvatarField(upload_to=b'images/projects/', null=True, verbose_name='logo', blank=True),
        ),
    ]
