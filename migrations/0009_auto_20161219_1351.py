# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0008_projectmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='curriculum',
            field=models.ForeignKey(related_name='curriculum', verbose_name='curriculum', blank=True, to='commons.Document', null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='mentoring',
            field=models.TextField(verbose_name='mentor presentation', blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='skype',
            field=models.CharField(max_length=50, null=True, verbose_name='skype id', blank=True),
        ),
    ]
