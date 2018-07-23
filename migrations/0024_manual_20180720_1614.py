# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields

from django.utils.text import slugify
from commons.utils import random_string_generator
from commons.models import Folder, FolderDocument

def unique_slug_generator(instance, slug):
    Klass = instance.__class__
    if Klass.objects.filter(slug=slug).exists():
        new_slug = "{slug}-{randstr}".format(
                    slug=slug,
                    randstr=random_string_generator(size=4)
                )
        if Klass.objects.filter(slug=new_slug).exists():
            return unique_slug_generator(instance, slug)
        slug = new_slug
    return slug

def gen_folder_slugs(apps, schema_editor):
    folders = Folder.objects.all()
    for folder in folders:
        slug = slugify(folder.get_title())
        folder.slug = unique_slug_generator(folder, slug)
        folder.save()

def gen_folderdocument_slugs(apps, schema_editor):
    folderdocuments = FolderDocument.objects.all()
    for folderdocument in folderdocuments:
        slug = slugify(folderdocument.__str__())
        folderdocument.slug = unique_slug_generator(folderdocument, slug)
        folderdocument.save()

class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0023_auto_20180720_1607'),
    ]

    operations = [
      migrations.RunPython(gen_folder_slugs),
      migrations.RunPython(gen_folderdocument_slugs),
    ]
