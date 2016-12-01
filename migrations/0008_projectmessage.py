# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_messages', '__first__'),
        ('commons', '0007_auto_20161119_1236'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.ForeignKey(related_name='project_message', verbose_name='message', to='django_messages.Message')),
                ('project', models.ForeignKey(related_name='message_project', verbose_name='project', to='commons.Project')),
            ],
            options={
                'verbose_name': 'project message',
                'verbose_name_plural': 'project messages',
            },
        ),
    ]
