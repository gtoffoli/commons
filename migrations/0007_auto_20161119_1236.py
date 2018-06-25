# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('commons', '0006_pathedge_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='SharedLearningPath',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('lp', models.ForeignKey(on_delete=models.CASCADE, verbose_name='referenced Learning Path', to='commons.LearningPath')),
                ('project', models.ForeignKey(on_delete=models.CASCADE, verbose_name='referencing project', to='commons.Project')),
                ('user', models.ForeignKey(on_delete=models.CASCADE, verbose_name='last editor', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'shared Learning Path',
                'verbose_name_plural': 'shared Learning Paths',
            },
        ),
        migrations.AlterUniqueTogether(
            name='sharedlearningpath',
            unique_together=set([('lp', 'project')]),
        ),
    ]
