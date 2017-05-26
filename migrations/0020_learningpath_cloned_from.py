# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0019_folderdocument_created'),
    ]

    operations = [
        migrations.AddField(
            model_name='learningpath',
            name='cloned_from',
            field=models.ForeignKey(related_name='cloned_path', verbose_name='original learning path', blank=True, to='commons.LearningPath', null=True),
        ),
    ]
