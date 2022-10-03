# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0020_learningpath_cloned_from'),
    ]

    operations = [
        migrations.AlterField(
            model_name='featured',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='featured',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),
        migrations.AlterField(
            model_name='featured',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='User', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='folder',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='folder',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='User', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='folderdocument',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created', null=True),
        ),
        migrations.AlterField(
            model_name='folderdocument',
            name='folder',
            field=models.ForeignKey(related_name='folderdocument_folder', on_delete=django.db.models.deletion.PROTECT, verbose_name='folder', to='commons.Folder'),
        ),
        migrations.AlterField(
            model_name='folderdocument',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='learningpath',
            name='cloned_from',
            field=models.ForeignKey(related_name='cloned_path', on_delete=django.db.models.deletion.SET_NULL, verbose_name='original learning path', blank=True, to='commons.LearningPath', null=True),
        ),
        migrations.AlterField(
            model_name='learningpath',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='learningpath',
            name='creator',
            field=models.ForeignKey(related_name='path_creator', on_delete=django.db.models.deletion.PROTECT, verbose_name='creator', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='learningpath',
            name='editor',
            field=models.ForeignKey(related_name='path_editor', on_delete=django.db.models.deletion.PROTECT, verbose_name='last editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='learningpath',
            name='group',
            field=models.ForeignKey(related_name='lp_group', on_delete=django.db.models.deletion.PROTECT, verbose_name='group', blank=True, to='auth.Group', null=True),
        ),
        migrations.AlterField(
            model_name='learningpath',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),
        migrations.AlterField(
            model_name='learningpath',
            name='project',
            field=models.ForeignKey(related_name='lp_project', on_delete=django.db.models.deletion.PROTECT, verbose_name='project', blank=True, to='commons.Project', null=True),
        ),
        migrations.AlterField(
            model_name='oer',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='oer',
            name='creator',
            field=models.ForeignKey(related_name='oer_creator', on_delete=django.db.models.deletion.PROTECT, verbose_name='creator', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='oer',
            name='editor',
            field=models.ForeignKey(related_name='oer_editor', on_delete=django.db.models.deletion.PROTECT, verbose_name='last editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='oer',
            name='license',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='terms of use', blank=True, to='commons.LicenseNode', null=True),
        ),
        migrations.AlterField(
            model_name='oer',
            name='material',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='type of material', blank=True, to='commons.MaterialEntry', null=True),
        ),
        migrations.AlterField(
            model_name='oer',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),
        migrations.AlterField(
            model_name='oer',
            name='project',
            field=models.ForeignKey(related_name='oer_project', on_delete=django.db.models.deletion.PROTECT, to='commons.Project', help_text='where the OER has been cataloged or created'),
        ),
        migrations.AlterField(
            model_name='oer',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='source repository', blank=True, to='commons.Repo', null=True),
        ),
        migrations.AlterField(
            model_name='oerevaluation',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),
        migrations.AlterField(
            model_name='oerevaluation',
            name='user',
            field=models.ForeignKey(related_name='oer_evaluator', on_delete=django.db.models.deletion.PROTECT, verbose_name='evaluator', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='oermetadata',
            name='metadata_type',
            field=models.ForeignKey(related_name='metadata_type', on_delete=django.db.models.deletion.PROTECT, verbose_name='Metadatum type', to='commons.MetadataType'),
        ),
        migrations.AlterField(
            model_name='oerqualitymetadata',
            name='quality_facet',
            field=models.ForeignKey(related_name='quality_facet', on_delete=django.db.models.deletion.PROTECT, verbose_name='quality facet', to='commons.QualityFacet'),
        ),
        migrations.AlterField(
            model_name='pathedge',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='pathedge',
            name='creator',
            field=models.ForeignKey(related_name='pathedge_creator', on_delete=django.db.models.deletion.PROTECT, verbose_name='creator', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='pathedge',
            name='editor',
            field=models.ForeignKey(related_name='pathedge_editor', on_delete=django.db.models.deletion.PROTECT, verbose_name='last editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='pathedge',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),
        migrations.AlterField(
            model_name='pathnode',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='pathnode',
            name='creator',
            field=models.ForeignKey(related_name='pathnode_creator', on_delete=django.db.models.deletion.PROTECT, verbose_name='creator', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='pathnode',
            name='document',
            field=models.ForeignKey(related_name='pathnode_document', on_delete=django.db.models.deletion.SET_NULL, verbose_name='document', blank=True, to='commons.Document', null=True),
        ),
        migrations.AlterField(
            model_name='pathnode',
            name='editor',
            field=models.ForeignKey(related_name='pathnode_editor', on_delete=django.db.models.deletion.PROTECT, verbose_name='last editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='pathnode',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),
        migrations.AlterField(
            model_name='pathnode',
            name='oer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='stands for', blank=True, to='commons.OER', null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='project',
            name='creator',
            field=models.ForeignKey(related_name='project_creator', on_delete=django.db.models.deletion.PROTECT, verbose_name='creator', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='project',
            name='editor',
            field=models.ForeignKey(related_name='project_editor', on_delete=django.db.models.deletion.PROTECT, verbose_name='last editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='project',
            name='forum',
            field=models.ForeignKey(related_name='project_forum', on_delete=django.db.models.deletion.SET_NULL, verbose_name='project forum', blank=True, to='pybb.Forum', null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='group',
            field=models.OneToOneField(related_name='project', on_delete=django.db.models.deletion.PROTECT, verbose_name='associated user group', to='auth.Group'),
        ),
        migrations.AlterField(
            model_name='project',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),
        migrations.AlterField(
            model_name='project',
            name='proj_type',
            field=models.ForeignKey(related_name='projects', on_delete=django.db.models.deletion.PROTECT, verbose_name='Project type', to='commons.ProjType'),
        ),
        migrations.AlterField(
            model_name='project',
            name='prototype',
            field=models.ForeignKey(related_name='prototype_project', on_delete=django.db.models.deletion.SET_NULL, verbose_name='prototypical Learning Path', blank=True, to='commons.LearningPath', null=True),
        ),
        migrations.AlterField(
            model_name='projectmember',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='request created'),
        ),
        migrations.AlterField(
            model_name='projectmember',
            name='editor',
            field=models.ForeignKey(related_name='membership_editor', on_delete=django.db.models.deletion.PROTECT, verbose_name='last state modifier', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='projectmember',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='last state change'),
        ),
        migrations.AlterField(
            model_name='projectmember',
            name='user',
            field=models.ForeignKey(related_name='membership_user', on_delete=django.db.models.deletion.PROTECT, verbose_name='user', to=settings.AUTH_USER_MODEL, help_text='the user belonging or applying to the project'),
        ),
        migrations.AlterField(
            model_name='repo',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='repo',
            name='creator',
            field=models.ForeignKey(related_name='repo_creator', on_delete=django.db.models.deletion.PROTECT, verbose_name='creator', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='repo',
            name='editor',
            field=models.ForeignKey(related_name='repo_editor', on_delete=django.db.models.deletion.PROTECT, verbose_name='last editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='repo',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified'),
        ),
        migrations.AlterField(
            model_name='repo',
            name='repo_type',
            field=models.ForeignKey(related_name='repositories', on_delete=django.db.models.deletion.PROTECT, verbose_name='repository type', to='commons.RepoType'),
        ),
        migrations.AlterField(
            model_name='sharedlearningpath',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='sharedlearningpath',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='referencing project', to='commons.Project'),
        ),
        migrations.AlterField(
            model_name='sharedlearningpath',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='last editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='sharedoer',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created'),
        ),
        migrations.AlterField(
            model_name='sharedoer',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='referencing project', to='commons.Project'),
        ),
        migrations.AlterField(
            model_name='sharedoer',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='last editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='country', blank=True, to='commons.CountryEntry', null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='curriculum',
            field=models.ForeignKey(related_name='profile_curriculum', on_delete=django.db.models.deletion.SET_NULL, verbose_name='curriculum', blank=True, to='commons.Document', null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='edu_field',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='field of study', blank=True, to='commons.EduFieldEntry', null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='edu_level',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='education level', blank=True, to='commons.EduLevelEntry', null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='pro_field',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='work sector', blank=True, to='commons.ProFieldEntry', null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='pro_status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='study or work status', blank=True, to='commons.ProStatusNode', null=True),
        ),
    ]
