# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0015_auto_20170223_1111'),
    ]

    operations = [
        migrations.AlterField(
            model_name='learningpath',
            name='slug',
            field=django_extensions.db.fields.AutoSlugField(editable=False, populate_from='title', max_length=80, blank=True, unique=True, overwrite=True),
        ),
        migrations.AlterField(
            model_name='oer',
            name='slug',
            field=django_extensions.db.fields.AutoSlugField(editable=False, populate_from='title', max_length=80, blank=True, unique=True, overwrite=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='slug',
            field=django_extensions.db.fields.AutoSlugField(editable=False, populate_from='name', max_length=80, blank=True, unique=True, overwrite=True),
        ),
        migrations.AlterField(
            model_name='repo',
            name='slug',
            field=django_extensions.db.fields.AutoSlugField(editable=False, populate_from='name', max_length=80, blank=True, unique=True, overwrite=True),
        ),
    ]
