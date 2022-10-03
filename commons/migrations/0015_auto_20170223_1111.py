# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0014_auto_20170223_1103'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='folder',
            unique_together=set([]),
        ),
    ]
