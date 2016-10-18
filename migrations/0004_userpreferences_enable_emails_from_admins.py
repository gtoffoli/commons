# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0003_auto_20160930_1319'),
    ]

    operations = [
        migrations.AddField(
            model_name='userpreferences',
            name='enable_emails_from_admins',
            field=models.BooleanField(default=True, help_text='Occasionally the CommonSpaces administrators will do some mailing without disclosing email addresses to anybody.', verbose_name='accept emails from administrators'),
        ),
    ]
