# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='learningpath',
            name='comment_count',
        ),
        migrations.RemoveField(
            model_name='oer',
            name='comment_count',
        ),
        migrations.RemoveField(
            model_name='project',
            name='comment_count',
        ),
        migrations.RemoveField(
            model_name='repo',
            name='comment_count',
        ),
    ]
