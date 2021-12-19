# Generated by Django 2.1.3 on 2021-12-19 22:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0029_auto_20211029_2329'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='siteobject',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='siteobject',
            name='site',
        ),
        migrations.AddField(
            model_name='pathnode',
            name='embed_code',
            field=models.TextField(blank=True, help_text='code to embed an online document, such as a GoogleDoc', null=True, verbose_name='embed code'),
        ),
        migrations.DeleteModel(
            name='SiteObject',
        ),
    ]
