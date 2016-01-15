# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields
import taggit.managers
import commons.models
import mptt.fields
import commons.documents
import django_dag.models
import django.utils.timezone
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
        ('dmuc', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    #   ('auth', '0007_auto_20160115_1014'),
    #   ('pybb', '0005_auto_20160115_1014'),

    operations = [
        migrations.CreateModel(
            name='AccessibilityEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('order', models.IntegerField(default=100)),
            ],
            options={
                'verbose_name': 'accessibility feature',
                'verbose_name_plural': 'accessibility features',
            },
        ),
        migrations.CreateModel(
            name='CountryEntry',
            fields=[
                ('code', models.CharField(max_length=5, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'country',
                'verbose_name_plural': 'countries',
            },
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(default=commons.documents.UUID_FUNCTION, max_length=48, editable=False)),
                ('label', models.CharField(default='Uninitialized document', help_text='The name of the document', max_length=255, verbose_name='Label', db_index=True)),
                ('description', models.TextField(null=True, verbose_name='Description', blank=True)),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='Added')),
                ('language', models.CharField(default='en', max_length=8, verbose_name='Language', choices=[(b'en', 'English'), (b'it', 'Italian'), (b'pt', 'Portuguese')])),
            ],
            options={
                'ordering': ['-date_added'],
                'verbose_name': 'Document',
                'verbose_name_plural': 'Documents',
            },
        ),
        migrations.CreateModel(
            name='DocumentType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=32, verbose_name='Name')),
                ('ocr', models.BooleanField(default=True, verbose_name='Automatically queue newly created documents for OCR.')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Document type',
                'verbose_name_plural': 'Documents types',
            },
        ),
        migrations.CreateModel(
            name='DocumentVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Timestamp')),
                ('comment', models.TextField(verbose_name='Comment', blank=True)),
                ('file', models.FileField(upload_to=commons.documents.UUID_FUNCTION, storage=commons.documents.FileBasedStorage(), verbose_name='File')),
                ('mimetype', models.CharField(max_length=255, null=True, editable=False, blank=True)),
                ('encoding', models.CharField(max_length=64, null=True, editable=False, blank=True)),
                ('checksum', models.TextField(verbose_name='Checksum', null=True, editable=False, blank=True)),
                ('document', models.ForeignKey(related_name='versions', verbose_name='Document', to='commons.Document')),
            ],
            options={
                'verbose_name': 'Document version',
                'verbose_name_plural': 'Document version',
            },
        ),
        migrations.CreateModel(
            name='EduFieldEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('order', models.IntegerField(default=100)),
            ],
            options={
                'verbose_name': 'education field',
                'verbose_name_plural': 'education fields',
            },
        ),
        migrations.CreateModel(
            name='EduLevelEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('order', models.IntegerField(default=100)),
            ],
            options={
                'verbose_name': 'education level',
                'verbose_name_plural': 'education levels',
            },
        ),
        migrations.CreateModel(
            name='Folder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=128, verbose_name='Title', db_index=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
            ],
            options={
                'ordering': ('title',),
                'verbose_name': 'folder',
                'verbose_name_plural': 'folders',
            },
        ),
        migrations.CreateModel(
            name='FolderDocument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField()),
                ('label', models.TextField(null=True, verbose_name='label', blank=True)),
                ('state', models.IntegerField(default=1, null=True, verbose_name=b'publication state', choices=[(1, 'Draft'), (2, 'Submitted'), (3, 'Published'), (4, 'Un-published')])),
                ('document', models.ForeignKey(related_name='folderdocument_document', verbose_name='document', to='commons.Document')),
                ('folder', models.ForeignKey(related_name='folderdocument_folder', verbose_name='folder', to='commons.Folder')),
            ],
            options={
                'verbose_name': 'folder document',
                'verbose_name_plural': 'folder documents',
            },
            bases=(models.Model, commons.models.Publishable),
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('code', models.CharField(max_length=5, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'OER language',
                'verbose_name_plural': 'OER languages',
            },
        ),
        migrations.CreateModel(
            name='LearningPath',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(editable=False, populate_from=b'title', blank=True, unique=True)),
                ('title', models.CharField(max_length=200, verbose_name='title', db_index=True)),
                ('path_type', models.IntegerField(choices=[(1, 'simple collection'), (2, 'sequence'), (3, 'directed graph'), (4, 'scripted directed graph')], verbose_name=b'path type', validators=[django.core.validators.MinValueValidator(1)])),
                ('short', models.TextField(verbose_name='objectives', blank=True)),
                ('long', models.TextField(verbose_name='description', blank=True)),
                ('state', models.IntegerField(default=1, null=True, verbose_name=b'publication state', choices=[(1, 'Draft'), (2, 'Submitted'), (3, 'Published'), (4, 'Un-published')])),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
            ],
            options={
                'verbose_name': 'learning path',
                'verbose_name_plural': 'learning paths',
            },
            bases=(models.Model, commons.models.Publishable),
        ),
        migrations.CreateModel(
            name='LevelNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('order', models.IntegerField(default=100)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(related_name='children', blank=True, to='commons.LevelNode', null=True)),
            ],
            options={
                'verbose_name': 'level',
                'verbose_name_plural': 'levels',
            },
        ),
        migrations.CreateModel(
            name='LicenseNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('order', models.IntegerField(default=100)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(related_name='children', blank=True, to='commons.LicenseNode', null=True)),
            ],
            options={
                'verbose_name': 'license',
                'verbose_name_plural': 'licenses',
            },
        ),
        migrations.CreateModel(
            name='MaterialEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('order', models.IntegerField(default=100)),
            ],
            options={
                'verbose_name': 'material type',
                'verbose_name_plural': 'material types',
            },
        ),
        migrations.CreateModel(
            name='MediaEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('order', models.IntegerField(default=100)),
            ],
            options={
                'verbose_name': 'media format',
                'verbose_name_plural': 'media formats',
            },
        ),
        migrations.CreateModel(
            name='MetadataType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='Do not use python reserved words, or spaces.', unique=True, max_length=48, verbose_name='Name')),
                ('title', models.CharField(max_length=48, verbose_name='Title')),
                ('default', models.CharField(help_text='Enter a string to be evaluated.', max_length=128, null=True, verbose_name='Default', blank=True)),
                ('lookup', models.TextField(help_text='Enter a string to be evaluated that returns an iterable.', null=True, verbose_name='Lookup', blank=True)),
                ('validation', models.CharField(blank=True, max_length=64, verbose_name='Validation function name', choices=[(b'Parse date', b'Parse date'), (b'Parse date and time', b'Parse date and time'), (b'Parse time', b'Parse time')])),
            ],
            options={
                'ordering': ('title',),
                'verbose_name': 'Metadata type',
                'verbose_name_plural': 'Metadata types',
            },
        ),
        migrations.CreateModel(
            name='NetworkEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('order', models.IntegerField(default=100)),
            ],
            options={
                'verbose_name': 'social network',
                'verbose_name_plural': 'social networks',
            },
        ),
        migrations.CreateModel(
            name='OER',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(editable=False, populate_from=b'title', blank=True, unique=True)),
                ('title', models.CharField(max_length=200, verbose_name='title', db_index=True)),
                ('description', models.TextField(null=True, verbose_name='abstract or description', blank=True)),
                ('oer_type', models.IntegerField(choices=[(1, 'Metadata only'), (2, 'Metadata and online reference'), (3, 'Metadata and document(s)')], verbose_name=b'OER type', validators=[django.core.validators.MinValueValidator(1)])),
                ('source_type', models.IntegerField(choices=[(1, 'Catalogued source'), (2, 'Non-catalogued source'), (3, 'Derived-translated'), (4, 'Derived-adapted'), (5, 'Derived-remixed'), (6, 'none (brand new OER)')], verbose_name=b'source type', validators=[django.core.validators.MinValueValidator(1)])),
                ('url', models.CharField(blank=True, max_length=200, null=True, help_text='specific URL to the OER, if applicable', validators=[django.core.validators.URLValidator()])),
                ('reference', models.TextField(help_text='other info to identify/access the OER in the source', null=True, verbose_name='reference', blank=True)),
                ('embed_code', models.TextField(help_text='code to embed the OER view in an HTML page', null=True, verbose_name='embed code', blank=True)),
                ('state', models.IntegerField(default=1, null=True, verbose_name=b'publication state', choices=[(1, 'Draft'), (2, 'Submitted'), (3, 'Published'), (4, 'Un-published')])),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('accessibility', models.ManyToManyField(to='commons.AccessibilityEntry', verbose_name=b'accessibility features', blank=True)),
            ],
            options={
                'verbose_name': 'OER',
                'verbose_name_plural': 'OERs',
            },
            bases=(models.Model, commons.models.Publishable),
        ),
        migrations.CreateModel(
            name='OerDocument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField()),
                ('document', models.ForeignKey(related_name='document', verbose_name='Document', to='commons.Document')),
                ('oer', models.ForeignKey(related_name='oer', verbose_name='OER', to='commons.OER')),
            ],
            options={
                'verbose_name': 'attached document',
                'verbose_name_plural': 'attached documents',
            },
        ),
        migrations.CreateModel(
            name='OerEvaluation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('overall_score', models.IntegerField(verbose_name=b'overall quality assessment', choices=[(b'', b'---------'), (1, 'poor'), (2, 'fair'), (3, 'good'), (4, 'very good'), (5, 'excellent')])),
                ('review', models.TextField(null=True, verbose_name='free text review', blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('oer', models.ForeignKey(related_name='evaluated_oer', verbose_name='OER', to='commons.OER')),
            ],
            options={
                'verbose_name': 'OER evaluation',
                'verbose_name_plural': 'OER evaluations',
            },
        ),
        migrations.CreateModel(
            name='OerMetadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(db_index=True, max_length=255, null=True, verbose_name='Value', blank=True)),
                ('metadata_type', models.ForeignKey(related_name='metadata_type', verbose_name='Metadatum type', to='commons.MetadataType')),
                ('oer', models.ForeignKey(related_name='metadata_set', verbose_name='OER', to='commons.OER')),
            ],
            options={
                'verbose_name': 'additional metadatum',
                'verbose_name_plural': 'additional metadata',
            },
        ),
        migrations.CreateModel(
            name='OerQualityMetadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.IntegerField(verbose_name='facet-related score', choices=[(b'', b'---------'), (1, 'poor'), (2, 'fair'), (3, 'good'), (4, 'very good'), (5, 'excellent')])),
                ('oer_evaluation', models.ForeignKey(related_name='oer_evaluation', verbose_name='OER evaluation', to='commons.OerEvaluation')),
            ],
            options={
                'verbose_name': 'quality metadatum',
                'verbose_name_plural': 'quality metadata',
            },
        ),
        migrations.CreateModel(
            name='PathEdge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.TextField(verbose_name='label', blank=True)),
                ('content', models.TextField(verbose_name='content', blank=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
            ],
            options={
                'verbose_name': 'path edge',
                'verbose_name_plural': 'path edges',
            },
        ),
        migrations.CreateModel(
            name='PathNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.TextField(verbose_name='label', blank=True)),
                ('range', models.TextField(null=True, verbose_name='display range', blank=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('children', models.ManyToManyField(related_name='_parents', null=True, through='commons.PathEdge', to='commons.PathNode', blank=True)),
            ],
            options={
                'verbose_name': 'path node',
                'verbose_name_plural': 'path nodes',
            },
            bases=(models.Model, django_dag.models.NodeBase),
        ),
        migrations.CreateModel(
            name='ProFieldEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('order', models.IntegerField(default=100)),
            ],
            options={
                'verbose_name': 'professional field',
                'verbose_name_plural': 'professional fields',
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('slug', django_extensions.db.fields.AutoSlugField(editable=False, populate_from=b'name', blank=True, unique=True)),
                ('chat_type', models.IntegerField(default=0, null=True, verbose_name=b'chat type', choices=[(0, 'no chatroom'), (1, 'permanent chatroom')])),
                ('description', models.TextField(null=True, verbose_name='short description', blank=True)),
                ('info', models.TextField(null=True, verbose_name='longer description', blank=True)),
                ('state', models.IntegerField(default=0, null=True, verbose_name=b'project state', choices=[(0, 'draft proposal'), (1, 'proposal submitted'), (2, 'project open'), (3, 'project closed'), (4, 'project deleted')])),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('chat_room', models.ForeignKey(related_name='project', verbose_name='chatroom', blank=True, to='dmuc.Room', null=True)),
            ],
            options={
                'verbose_name': 'project / community',
                'verbose_name_plural': 'projects',
            },
        ),
        migrations.CreateModel(
            name='ProjectMember',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('state', models.IntegerField(default=0, null=True, verbose_name=b'membership state', choices=[(0, 'request submitted'), (1, 'request accepted'), (2, 'request rejected'), (3, 'membership suspended')])),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='request created', editable=False, blank=True)),
                ('accepted', models.DateTimeField(default=None, null=True, verbose_name='last acceptance')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='last state change', editable=False, blank=True)),
                ('history', models.TextField(null=True, verbose_name='history of state changes', blank=True)),
            ],
            options={
                'verbose_name': 'project member',
                'verbose_name_plural': 'project member',
            },
        ),
        migrations.CreateModel(
            name='ProjType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=20, verbose_name='name')),
                ('description', models.CharField(max_length=100, verbose_name='description')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='sort order')),
                ('public', models.BooleanField(default=False, verbose_name='public')),
            ],
            options={
                'ordering': ['order', 'name'],
                'verbose_name': 'project / community type',
                'verbose_name_plural': 'project / community types',
            },
        ),
        migrations.CreateModel(
            name='ProStatusNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('order', models.IntegerField(default=100)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(related_name='children', blank=True, to='commons.ProStatusNode', null=True)),
            ],
            options={
                'verbose_name': 'study or work status',
                'verbose_name_plural': 'study or work statuses',
            },
        ),
        migrations.CreateModel(
            name='QualityFacet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('order', models.IntegerField(default=100)),
            ],
            options={
                'verbose_name': 'quality facet',
                'verbose_name_plural': 'quality facets',
            },
        ),
        migrations.CreateModel(
            name='Repo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', db_index=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(editable=False, populate_from=b'name', blank=True, unique=True)),
                ('url', models.CharField(blank=True, max_length=200, null=True, verbose_name='URL of the repository site', validators=[django.core.validators.URLValidator()])),
                ('description', models.TextField(null=True, verbose_name='short description', blank=True)),
                ('info', models.TextField(null=True, verbose_name='longer description / search suggestions', blank=True)),
                ('eval', models.TextField(null=True, verbose_name='comments / evaluation', blank=True)),
                ('state', models.IntegerField(default=1, null=True, verbose_name=b'publication state', choices=[(1, 'Draft'), (2, 'Submitted'), (3, 'Published'), (4, 'Un-published')])),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
            ],
            options={
                'verbose_name': 'external repository',
                'verbose_name_plural': 'external repositories',
            },
            bases=(models.Model, commons.models.Publishable),
        ),
        migrations.CreateModel(
            name='RepoFeature',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='sort order')),
            ],
            options={
                'ordering': ['order'],
                'verbose_name': 'repository feature',
                'verbose_name_plural': 'repository features',
            },
        ),
        migrations.CreateModel(
            name='RepoType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=20, verbose_name='name')),
                ('description', models.CharField(max_length=100, verbose_name='description')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='sort order')),
            ],
            options={
                'ordering': ['order', 'name'],
                'verbose_name': 'repository type',
                'verbose_name_plural': 'repository types',
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('code', models.CharField(max_length=10, serialize=False, verbose_name='code', primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='name')),
            ],
            options={
                'ordering': ['code'],
                'verbose_name': 'subject',
                'verbose_name_plural': 'subjects',
            },
        ),
        migrations.CreateModel(
            name='SubjectNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('order', models.IntegerField(default=100)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(related_name='children', blank=True, to='commons.SubjectNode', null=True)),
            ],
            options={
                'verbose_name': 'subject',
                'verbose_name_plural': 'subjects',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('user', models.OneToOneField(related_name='profile', primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('gender', models.CharField(default=b'-', max_length=1, null=True, blank=True, choices=[(b'-', 'not specified'), (b'm', 'male'), (b'f', 'female')])),
                ('dob', models.DateField(help_text='format: dd/mm/yyyy', null=True, verbose_name='date of birth', blank=True)),
                ('city', models.CharField(max_length=250, null=True, verbose_name='city', blank=True)),
                ('position', models.TextField(null=True, verbose_name='study or work position', blank=True)),
                ('other_languages', models.TextField(help_text='list one per line.', verbose_name='known languages not listed above', blank=True)),
                ('short', models.TextField(verbose_name='short presentation', blank=True)),
                ('long', models.TextField(verbose_name='longer presentation', blank=True)),
                ('url', models.CharField(blank=True, max_length=200, verbose_name='web site', validators=[django.core.validators.URLValidator()])),
                ('avatar', models.ImageField(upload_to=b'images/avatars/', null=True, verbose_name=b'profile picture', blank=True)),
                ('enable_email_notifications', models.PositiveIntegerField(default=0, null=True, verbose_name='email notifications', choices=[(0, 'do not notify me of new private messages'), (1, 'notify me only of individual messages'), (2, 'notify me of individual and group messages')])),
                ('country', models.ForeignKey(verbose_name='country', blank=True, to='commons.CountryEntry', null=True)),
                ('edu_field', models.ForeignKey(verbose_name='field of study', blank=True, to='commons.EduFieldEntry', null=True)),
                ('edu_level', models.ForeignKey(verbose_name='education level', blank=True, to='commons.EduLevelEntry', null=True)),
                ('languages', models.ManyToManyField(help_text='The UI will support only EN, IT and PT.', to='commons.Language', verbose_name=b'known languages', blank=True)),
                ('networks', models.ManyToManyField(to='commons.NetworkEntry', verbose_name='online networks / services used', blank=True)),
                ('pro_field', models.ForeignKey(verbose_name='work sector', blank=True, to='commons.ProFieldEntry', null=True)),
                ('pro_status', models.ForeignKey(verbose_name='study or work status', blank=True, to='commons.ProStatusNode', null=True)),
                ('subjects', models.ManyToManyField(to='commons.SubjectNode', verbose_name=b'interest areas', blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='repo',
            name='creator',
            field=models.ForeignKey(related_name='repo_creator', verbose_name='creator', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='repo',
            name='editor',
            field=models.ForeignKey(related_name='repo_editor', verbose_name='last editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='repo',
            name='features',
            field=models.ManyToManyField(to='commons.RepoFeature', verbose_name=b'repository features', blank=True),
        ),
        migrations.AddField(
            model_name='repo',
            name='languages',
            field=models.ManyToManyField(to='commons.Language', verbose_name=b'languages of documents', blank=True),
        ),
        migrations.AddField(
            model_name='repo',
            name='repo_type',
            field=models.ForeignKey(related_name='repositories', verbose_name='repository type', to='commons.RepoType'),
        ),
        migrations.AddField(
            model_name='repo',
            name='subjects',
            field=models.ManyToManyField(to='commons.SubjectNode', verbose_name=b'Subject areas', blank=True),
        ),
        migrations.AddField(
            model_name='projectmember',
            name='editor',
            field=models.ForeignKey(related_name='membership_editor', verbose_name='last state modifier', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='projectmember',
            name='project',
            field=models.ForeignKey(verbose_name='community or project', to='commons.Project', help_text='the project the user belongs or applies to'),
        ),
        migrations.AddField(
            model_name='projectmember',
            name='user',
            field=models.ForeignKey(related_name='membership_user', verbose_name='user', to=settings.AUTH_USER_MODEL, help_text='the user belonging or applying to the project'),
        ),
        migrations.AddField(
            model_name='project',
            name='creator',
            field=models.ForeignKey(related_name='project_creator', verbose_name='creator', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='project',
            name='editor',
            field=models.ForeignKey(related_name='project_editor', verbose_name='last editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='project',
            name='folders',
            field=models.ManyToManyField(related_name='project', verbose_name='folders', to='commons.Folder'),
        ),
        migrations.AddField(
            model_name='project',
            name='forum',
            field=models.ForeignKey(related_name='project_forum', verbose_name='project forum', blank=True, to='pybb.Forum', null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='group',
            field=models.OneToOneField(related_name='project', verbose_name='associated user group', to='auth.Group'),
        ),
        migrations.AddField(
            model_name='project',
            name='proj_type',
            field=models.ForeignKey(related_name='projects', verbose_name='Project type', to='commons.ProjType'),
        ),
        migrations.AddField(
            model_name='pathnode',
            name='creator',
            field=models.ForeignKey(related_name='pathnode_creator', verbose_name='creator', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='pathnode',
            name='editor',
            field=models.ForeignKey(related_name='pathnode_editor', verbose_name='last editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='pathnode',
            name='oer',
            field=models.ForeignKey(verbose_name='stands for', to='commons.OER'),
        ),
        migrations.AddField(
            model_name='pathnode',
            name='path',
            field=models.ForeignKey(verbose_name='learning path or collection', to='commons.LearningPath'),
        ),
        migrations.AddField(
            model_name='pathedge',
            name='child',
            field=models.ForeignKey(related_name='PathNode_parent', to='commons.PathNode'),
        ),
        migrations.AddField(
            model_name='pathedge',
            name='creator',
            field=models.ForeignKey(related_name='pathedge_creator', verbose_name='creator', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='pathedge',
            name='editor',
            field=models.ForeignKey(related_name='pathedge_editor', verbose_name='last editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='pathedge',
            name='parent',
            field=models.ForeignKey(related_name='PathNode_child', to='commons.PathNode'),
        ),
        migrations.AddField(
            model_name='oerqualitymetadata',
            name='quality_facet',
            field=models.ForeignKey(related_name='quality_facet', verbose_name='quality facet', to='commons.QualityFacet'),
        ),
        migrations.AddField(
            model_name='oerevaluation',
            name='quality_metadata',
            field=models.ManyToManyField(related_name='quality_metadata', verbose_name=b'quality metadata', to='commons.QualityFacet', through='commons.OerQualityMetadata', blank=True),
        ),
        migrations.AddField(
            model_name='oerevaluation',
            name='user',
            field=models.ForeignKey(verbose_name='last editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='oer',
            name='creator',
            field=models.ForeignKey(related_name='oer_creator', verbose_name='creator', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='oer',
            name='documents',
            field=models.ManyToManyField(related_name='oer_document', verbose_name=b'attached documents', to='commons.Document', through='commons.OerDocument', blank=True),
        ),
        migrations.AddField(
            model_name='oer',
            name='editor',
            field=models.ForeignKey(related_name='oer_editor', verbose_name='last editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='oer',
            name='languages',
            field=models.ManyToManyField(to='commons.Language', verbose_name=b'languages of OER', blank=True),
        ),
        migrations.AddField(
            model_name='oer',
            name='levels',
            field=models.ManyToManyField(to='commons.LevelNode', verbose_name=b'Levels', blank=True),
        ),
        migrations.AddField(
            model_name='oer',
            name='license',
            field=models.ForeignKey(verbose_name='terms of use', blank=True, to='commons.LicenseNode', null=True),
        ),
        migrations.AddField(
            model_name='oer',
            name='material',
            field=models.ForeignKey(verbose_name='type of material', blank=True, to='commons.MaterialEntry', null=True),
        ),
        migrations.AddField(
            model_name='oer',
            name='media',
            field=models.ManyToManyField(to='commons.MediaEntry', verbose_name=b'media formats', blank=True),
        ),
        migrations.AddField(
            model_name='oer',
            name='metadata',
            field=models.ManyToManyField(related_name='oer_metadata', verbose_name=b'metadata', to='commons.MetadataType', through='commons.OerMetadata', blank=True),
        ),
        migrations.AddField(
            model_name='oer',
            name='oers',
            field=models.ManyToManyField(related_name='derived_from', verbose_name=b'derived from', to='commons.OER', blank=True),
        ),
        migrations.AddField(
            model_name='oer',
            name='project',
            field=models.ForeignKey(help_text='where the OER has been cataloged or created', to='commons.Project'),
        ),
        migrations.AddField(
            model_name='oer',
            name='source',
            field=models.ForeignKey(verbose_name='source repository', blank=True, to='commons.Repo', null=True),
        ),
        migrations.AddField(
            model_name='oer',
            name='subjects',
            field=models.ManyToManyField(to='commons.SubjectNode', verbose_name=b'Subject areas', blank=True),
        ),
        migrations.AddField(
            model_name='oer',
            name='tags',
            field=taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='comma separated strings; please try using suggestion of existing tags', verbose_name=b'tags'),
        ),
        migrations.AddField(
            model_name='learningpath',
            name='creator',
            field=models.ForeignKey(related_name='path_creator', verbose_name='creator', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='learningpath',
            name='editor',
            field=models.ForeignKey(related_name='path_editor', verbose_name='last editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='learningpath',
            name='group',
            field=models.ForeignKey(related_name='lp_group', verbose_name='group', blank=True, to='auth.Group', null=True),
        ),
        migrations.AddField(
            model_name='learningpath',
            name='levels',
            field=models.ManyToManyField(to='commons.LevelNode', verbose_name=b'Levels', blank=True),
        ),
        migrations.AddField(
            model_name='learningpath',
            name='project',
            field=models.ForeignKey(verbose_name='project', blank=True, to='commons.Project', null=True),
        ),
        migrations.AddField(
            model_name='learningpath',
            name='subjects',
            field=models.ManyToManyField(to='commons.SubjectNode', verbose_name=b'Subject areas', blank=True),
        ),
        migrations.AddField(
            model_name='learningpath',
            name='tags',
            field=taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='comma separated strings; please try using suggestion of existing tags', verbose_name=b'tags'),
        ),
        migrations.AddField(
            model_name='folderdocument',
            name='user',
            field=models.ForeignKey(verbose_name='user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='folder',
            name='documents',
            field=models.ManyToManyField(related_name='document_folder', verbose_name=b'documents', to='commons.Document', through='commons.FolderDocument', blank=True),
        ),
        migrations.AddField(
            model_name='folder',
            name='parent',
            field=mptt.fields.TreeForeignKey(related_name='subfolders', blank=True, to='commons.Folder', null=True),
        ),
        migrations.AddField(
            model_name='folder',
            name='user',
            field=models.ForeignKey(verbose_name='User', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='document',
            name='document_type',
            field=models.ForeignKey(related_name='documents', verbose_name='Document type', to='commons.DocumentType'),
        ),
        migrations.AlterUniqueTogether(
            name='oerqualitymetadata',
            unique_together=set([('oer_evaluation', 'quality_facet')]),
        ),
        migrations.AlterUniqueTogether(
            name='oermetadata',
            unique_together=set([('oer', 'metadata_type', 'value')]),
        ),
        migrations.AlterUniqueTogether(
            name='oerevaluation',
            unique_together=set([('oer', 'user')]),
        ),
        migrations.AlterUniqueTogether(
            name='oerdocument',
            unique_together=set([('oer', 'document')]),
        ),
        migrations.AlterUniqueTogether(
            name='folderdocument',
            unique_together=set([('folder', 'document')]),
        ),
        migrations.AlterUniqueTogether(
            name='folder',
            unique_together=set([('title', 'user')]),
        ),
    ]
