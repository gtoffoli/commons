from collections import defaultdict
from django.contrib.contenttypes.models import ContentType
from commons.vocabularies import MaterialEntry, MediaEntry, AccessibilityEntry, LevelNode, SubjectNode, LicenseNode
from commons.vocabularies import EduLevelEntry, ProStatusNode, EduFieldEntry, ProFieldEntry, NetworkEntry, Language, CountryEntry
from commons.models import OER, LearningPath, Tag, TaggedOER, TaggedLP

model_tagged_map = {
    LearningPath.__name__: TaggedLP,
    OER.__name__: TaggedOER,
}

"""
>>> from commons.scripts.metadata import popular_tags
>>> pt = popular_tags()
>>> for t in list(pt.values())
>>>   print(t['count'], t['TaggedLP'].count(). t['TaggedOER'].count(), t['tag'].slug, t['tag'].name)
"""
def popular_tags(models=(LearningPath, OER,)):
    tags = Tag.objects.all().order_by('name')
    tags_dict = {}
    for tag in tags:
        tag_dict = {'count': 0, 'tag': tag}
        for model in models:
            tagged_model = model_tagged_map[model.__name__]
            content_type = ContentType.objects.get(model=model.__name__.lower())
            tagged = tagged_model.objects.filter(tag=tag, content_type=content_type)
            tag_dict['count'] += tagged.count()
            tag_dict[tagged_model.__name__] = tagged
        tags_dict[tag.slug] = tag_dict
    return tags_dict

def replace_tag(tag_from_slug, tag_to_slug, models=(LearningPath, OER,)):
    tag_from = Tag.objects.get(slug=tag_from_slug)
    tag_to = Tag.objects.get(slug=tag_to_slug)
    for model in models:
        tagged_model = model_tagged_map[model.__name__]
        content_type = ContentType.objects.get(model=model.__name__.lower())
        tagged_from = tagged_model.objects.filter(content_type=content_type, tag=tag_from)
        for tagged in tagged_from:
            if tagged_model.objects.filter(object=tagged.object, tag=tag_to).count():
                tagged.delete()
            else:
                tagged.tag = tag_to
                tagged.save()
