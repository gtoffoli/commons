# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings
import django_extensions.db.fields
import awesome_avatar.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('commons', '0004_userpreferences_enable_emails_from_admins'),
    ]

    operations = [
        migrations.CreateModel(
            name='SharedOer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
            ],
            options={
                'verbose_name': 'shared OER',
                'verbose_name_plural': 'shared OERs',
            },
        ),
        migrations.AlterField(
            model_name='learningpath',
            name='big_image',
            field=awesome_avatar.fields.AvatarField(upload_to=b'images/lps/', null=True, verbose_name='featured image'),
        ),
        migrations.AlterField(
            model_name='learningpath',
            name='small_image',
            field=awesome_avatar.fields.AvatarField(upload_to=b'images/lps/', null=True, verbose_name='logo'),
        ),
        migrations.AlterField(
            model_name='oer',
            name='big_image',
            field=awesome_avatar.fields.AvatarField(upload_to=b'images/oers/', null=True, verbose_name=b''),
        ),
        migrations.AlterField(
            model_name='oer',
            name='small_image',
            field=awesome_avatar.fields.AvatarField(upload_to=b'images/oers/', null=True, verbose_name=b'screenshot'),
        ),
        migrations.AlterField(
            model_name='project',
            name='big_image',
            field=awesome_avatar.fields.AvatarField(upload_to=b'images/projects/', null=True, verbose_name='featured image'),
        ),
        migrations.AlterField(
            model_name='project',
            name='small_image',
            field=awesome_avatar.fields.AvatarField(upload_to=b'images/projects/', null=True, verbose_name='logo'),
        ),
        migrations.AlterField(
            model_name='repo',
            name='big_image',
            field=awesome_avatar.fields.AvatarField(upload_to=b'images/repo/', null=True, verbose_name='featured image'),
        ),
        migrations.AlterField(
            model_name='repo',
            name='small_image',
            field=awesome_avatar.fields.AvatarField(upload_to=b'images/repo/', null=True, verbose_name='screenshot'),
        ),
        migrations.AlterField(
            model_name='userpreferences',
            name='enable_email_notifications',
            field=models.PositiveIntegerField(default=0, help_text='Do you want that private messages from other members be notified to you by email? In any case, they will not know your email address.', null=True, verbose_name='email notifications', choices=[(0, 'do not notify me of new private messages'), (1, 'notify me only of individual messages'), (2, 'notify me of individual and group messages')]),
        ),
        migrations.AlterField(
            model_name='userpreferences',
            name='enable_emails_from_admins',
            field=models.BooleanField(default=True, help_text='Occasionally, the CommonSpaces administrators will do some mailing, without disclosing email addresses to anybody.', verbose_name='accept emails from administrators'),
        ),
        migrations.AddField(
            model_name='sharedoer',
            name='oer',
            field=models.ForeignKey(verbose_name='referenced OER', to='commons.OER'),
        ),
        migrations.AddField(
            model_name='sharedoer',
            name='project',
            field=models.ForeignKey(verbose_name='referencing project', to='commons.Project'),
        ),
        migrations.AddField(
            model_name='sharedoer',
            name='user',
            field=models.ForeignKey(verbose_name='last editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='sharedoer',
            unique_together=set([('oer', 'project')]),
        ),
    ]
