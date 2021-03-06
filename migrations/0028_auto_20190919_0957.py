# Generated by Django 2.1.3 on 2019-09-19 07:57

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0027_auto_20181002_1449'),
    ]

    operations = [
        migrations.AddField(
            model_name='oer',
            name='text',
            field=models.TextField(blank=True, null=True, verbose_name='own text content'),
        ),
        migrations.AlterField(
            model_name='featured',
            name='status',
            field=models.IntegerField(choices=[(-3, 'Portlet'), (-1, 'Grey'), (1, 'Draft'), (2, 'Submitted'), (3, 'Published'), (4, 'Un-published')], default=1, null=True, verbose_name='publication state'),
        ),
        migrations.AlterField(
            model_name='folderdocument',
            name='state',
            field=models.IntegerField(choices=[(-3, 'Portlet'), (-1, 'Grey'), (1, 'Draft'), (2, 'Submitted'), (3, 'Published'), (4, 'Un-published')], default=1, null=True, verbose_name='publication state'),
        ),
        migrations.AlterField(
            model_name='learningpath',
            name='state',
            field=models.IntegerField(choices=[(-3, 'Portlet'), (-1, 'Grey'), (1, 'Draft'), (2, 'Submitted'), (3, 'Published'), (4, 'Un-published')], default=1, null=True, verbose_name='publication state'),
        ),
        migrations.AlterField(
            model_name='metadatatype',
            name='validation',
            field=models.CharField(blank=True, choices=[('Parse date and time', 'Parse date and time'), ('Parse date', 'Parse date'), ('Parse time', 'Parse time')], max_length=64, verbose_name='Validation function name'),
        ),
        migrations.AlterField(
            model_name='oer',
            name='oer_type',
            field=models.IntegerField(choices=[(1, 'Metadata only'), (2, 'Metadata and online reference'), (3, 'Metadata and document(s)'), (4, 'Metadata and richtext')], default=2, validators=[django.core.validators.MinValueValidator(1)], verbose_name='OER type'),
        ),
        migrations.AlterField(
            model_name='oer',
            name='state',
            field=models.IntegerField(choices=[(-3, 'Portlet'), (-1, 'Grey'), (1, 'Draft'), (2, 'Submitted'), (3, 'Published'), (4, 'Un-published')], default=1, null=True, verbose_name='publication state'),
        ),
        migrations.AlterField(
            model_name='pathnode',
            name='children',
            field=models.ManyToManyField(blank=True, related_name='_parents', through='commons.PathEdge', to='commons.PathNode'),
        ),
        migrations.AlterField(
            model_name='repo',
            name='state',
            field=models.IntegerField(choices=[(-3, 'Portlet'), (-1, 'Grey'), (1, 'Draft'), (2, 'Submitted'), (3, 'Published'), (4, 'Un-published')], default=1, null=True, verbose_name='publication state'),
        ),
    ]
