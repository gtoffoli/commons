# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='reserved',
            field=models.BooleanField(default=False, verbose_name='reserved'),
        ),
        migrations.AlterField(
            model_name='project',
            name='chat_type',
            field=models.IntegerField(default=1, null=True, verbose_name=b'chat type', choices=[(0, 'no chatroom'), (1, 'permanent chatroom')]),
        ),
    ]
