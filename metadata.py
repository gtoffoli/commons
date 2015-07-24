from django.db import models
from django.utils.translation import ugettext_lazy as _
from dateutil.parser import parse


default_available_validators = {
    'Parse date and time': lambda input: parse(input).isoformat(),
    'Parse date': lambda input: parse(input).date().isoformat(),
    'Parse time': lambda input: parse(input).time().isoformat()
}
AVAILABLE_VALIDATORS = default_available_validators

class MetadataTypeManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)

class MetadataType(models.Model):
    """
    Define a type of metadata
    """
    name = models.CharField(unique=True, max_length=48, verbose_name=_('Name'), help_text=_('Do not use python reserved words, or spaces.'))
    # TODO: normalize 'title' to 'label'
    title = models.CharField(max_length=48, verbose_name=_('Title'))
    default = models.CharField(max_length=128, blank=True, null=True,
                               verbose_name=_('Default'),
                               help_text=_('Enter a string to be evaluated.'))
    # TODO: Add enable_lookup boolean to allow users to switch the lookup on and
    # off without losing the lookup expression
    lookup = models.TextField(blank=True, null=True,
                              verbose_name=_('Lookup'),
                              help_text=_('Enter a string to be evaluated that returns an iterable.'))
    validation = models.CharField(blank=True, choices=zip(AVAILABLE_VALIDATORS, AVAILABLE_VALIDATORS), max_length=64, verbose_name=_('Validation function name'))
    # TODO: Find a different way to let users know what models and functions are
    # available now that we removed these from the help_text
    objects = MetadataTypeManager()

    def __unicode__(self):
        return self.title

    def natural_key(self):
        return (self.name,)

    class Meta:
        ordering = ('title',)
        verbose_name = _('Metadata type')
        verbose_name_plural = _('Metadata types')


from django.contrib import admin

class MetadataTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'default', 'lookup', 'validation')


admin.site.register(MetadataType, MetadataTypeAdmin)
