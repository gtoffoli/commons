# from __future__ import unicode_literals
# from django.utils.encoding import python_2_unicode_compatible

from six import StringIO
# unicode = str

import hashlib
import logging
import os
import uuid

from django.core.files.storage import FileSystemStorage
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from commons.compressed_files import CompressedFile, NotACompressedFile
from commons.scorm import ContentPackage
import commons.utils
from django.conf import settings

# CACHE_PATH = os.path.join(settings.MEDIA_ROOT, 'image_cache')
LANGUAGE = 'en'
LANGUAGE_CHOICES = settings.LANGUAGES
# FILESTORAGE_LOCATION = os.path.join(settings.MEDIA_ROOT, 'document_storage')

HASH_FUNCTION = lambda x: hashlib.sha256(x).hexdigest()  # document image cache name hash function
# UUID_FUNCTION = lambda: unicode(uuid.uuid4())
def UUID_FUNCTION(*args, **kwargs):
    # return unicode(uuid.uuid4())
    return str(uuid.uuid4())
logger = logging.getLogger(__name__)

VIEWABLE_MIMETYPES = (
  'image/gif',
  'image/jpeg',
  'image/pjpeg',
  'image/png',
  'image/x-png',
  'audio/x-mpg',
  'audio/mpeg',
  'audio/mp3',
  'audio/mp4',
  'video/mp3',
  'video/mp4',
  'pdf',
  'opendocument.text',
  'opendocument.spreadsheet',
  'opendocument.presentation',
  'application/x-ipynb+json',
)

VIEWERJS_MIMETYPES = (
  'pdf',
  'opendocument.text',
  'opendocument.spreadsheet',
  'opendocument.presentation',
)

class FileBasedStorage(FileSystemStorage):
    """Simple wrapper for the stock Django FileSystemStorage class"""

    separator = os.path.sep

    def __init__(self, *args, **kwargs):
        super(FileBasedStorage, self).__init__(*args, **kwargs)
        # self.location = FILESTORAGE_LOCATION
        self.location = settings.FILESTORAGE_LOCATION

storage_backend = FileBasedStorage()

try:
    import magic
    USE_PYTHON_MAGIC = True
except:
    import mimetypes
    mimetypes.init()
    USE_PYTHON_MAGIC = False

def get_mimetype(file_description, filepath, mimetype_only=False):
    """
    Determine a file's mimetype by calling the system's libmagic
    library via python-magic or fallback to use python's mimetypes
    library
    """
    file_mimetype = None
    file_mime_encoding = None

    path, filename = os.path.split(filepath)
    if filename.endswith('ipynb'):
        file_mimetype = 'application/x-ipynb+json'

    elif USE_PYTHON_MAGIC:
        mime = magic.Magic(mime=True)
        file_mimetype = mime.from_buffer(file_description.read())
        if not mimetype_only:
            file_description.seek(0)
            mime_encoding = magic.Magic(mime_encoding=True)
            file_mime_encoding = mime_encoding.from_buffer(file_description.read())
    else:
        # path, filename = os.path.split(filepath)
        file_mimetype, file_mime_encoding = mimetypes.guess_type(filename)

    file_description.close()

    return file_mimetype, file_mime_encoding

class DocumentTypeManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)

# @python_2_unicode_compatible
class DocumentType(models.Model):
    """
    Define document types or classes to which a specific set of
    properties can be attached
    """
    class Meta:
        verbose_name = _('Document type')
        verbose_name_plural = _('Documents types')
        ordering = ['name']
        app_label = 'commons'

    name = models.CharField(max_length=32, verbose_name=_('Name'), unique=True)

    # TODO: find a way to move this to the ocr app
    ocr = models.BooleanField(default=True, verbose_name=_('Automatically queue newly created documents for OCR.'))

    objects = DocumentTypeManager()

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)

class DocumentManager(models.Manager):
    @transaction.atomic
    def new_document(self, document_type, file_object, label=None, command_line=False, description=None, expand=False, language=None, user=None):
        versions_created = []

        if expand:
            try:
                compressed_file = CompressedFile(file_object)
                count = 1
                for compressed_file_child in compressed_file.children():
                    if command_line:
                        print ('Uploading file #%d: %s' % (count, compressed_file_child))
                    # versions_created.append(self.upload_single_document(document_type=document_type, file_object=compressed_file_child, description=description, label=unicode(compressed_file_child), language=language or LANGUAGE, user=user))
                    versions_created.append(self.upload_single_document(document_type=document_type, file_object=compressed_file_child, description=description, label=str(compressed_file_child), language=language or LANGUAGE, user=user))
                    compressed_file_child.close()
                    count += 1

            except NotACompressedFile:
                logging.debug('Exception: NotACompressedFile')
                if command_line:
                    raise
                versions_created.append(self.upload_single_document(document_type=document_type, file_object=file_object, description=description, label=label, language=language or LANGUAGE, user=user))
        else:
            versions_created.append(self.upload_single_document(document_type=document_type, file_object=file_object, description=description, label=label, language=language or LANGUAGE, user=user))

        return versions_created

    @transaction.atomic
    def upload_single_document(self, document_type, file_object, label=None, description=None, language=None, user=None):
        # document = self.model(description=description, document_type=document_type, language=language, label=label or unicode(file_object))
        document = self.model(description=description, document_type=document_type, language=language, label=label or str(file_object))
        document.save(user=user)
        version = document.new_version(file_object=file_object, user=user)
        document.set_document_type(document_type, force=True)
        return version

# @python_2_unicode_compatible
class Document(models.Model):
    """
    Defines a single document with it's fields and properties
    """

    # uuid = models.CharField(default=lambda: UUID_FUNCTION(), max_length=48, editable=False)
    uuid = models.CharField(default=UUID_FUNCTION, max_length=48, editable=False)
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE, verbose_name=_('Document type'), related_name='documents')
    label = models.CharField(max_length=255, default=_('Uninitialized document'), db_index=True, help_text=_('The name of the document'), verbose_name=_('Label'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    date_added = models.DateTimeField(verbose_name=_('Added'), auto_now_add=True)
    language = models.CharField(choices=LANGUAGE_CHOICES, default=LANGUAGE, max_length=8, verbose_name=_('Language'))

    objects = DocumentManager()

    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
        ordering = ['-date_added']

    def set_document_type(self, document_type, force=False):
        # has_changed = self.document_type != document_type

        self.document_type = document_type
        self.save()
        """
        if has_changed or force:
            post_document_type_change.send(sender=self.__class__, instance=self)
        """

    """
    @staticmethod
    def clear_image_cache():
        for the_file in os.listdir(CACHE_PATH):
            file_path = os.path.join(CACHE_PATH, the_file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
    """

    def __str__(self):
        return self.label

    """
    @models.permalink
    def get_absolute_url(self):
        return ('documents:document_preview', [self.pk])
    """
    def get_absolute_url(self):
        return '/document/%d/view/' % self.pk

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        # new_document = not self.pk
        super(Document, self).save(*args, **kwargs)
        """

        if new_document:
            # apply_default_acls(self, user)

            if user:
                # self.add_as_recent_document_for_user(user)
                event_document_create.commit(actor=user, target=self)
            else:
                event_document_create.commit(target=self)
        """

    """
    def get_cached_image_name(self, page, version):
        document_version = DocumentVersion.objects.get(pk=version)
        document_page = document_version.pages.get(page_number=page)
        transformations, warnings = document_page.get_transformation_list()
        hash_value = HASH_FUNCTION(''.join([document_version.checksum, unicode(page), unicode(transformations)]))
        return os.path.join(CACHE_PATH, hash_value), transformations

    def get_image_cache_name(self, page, version):
        cache_file_path, transformations = self.get_cached_image_name(page, version)
        if os.path.exists(cache_file_path):
            return cache_file_path
        else:
            document_version = DocumentVersion.objects.get(pk=version)
            document_file = document_version.document.document_save_to_temp_dir(document_version.checksum)
            print 'document_file = ', document_file
            return convert(input_filepath=document_file, output_filepath=cache_file_path, page=page, transformations=transformations, mimetype=self.file_mimetype)

    def get_valid_image(self, size=DISPLAY_SIZE, page=DEFAULT_PAGE_NUMBER, zoom=DEFAULT_ZOOM_LEVEL, rotation=DEFAULT_ROTATION, version=None):
        if not version:
            version = self.latest_version.pk
        image_cache_name = self.get_image_cache_name(page=page, version=version)

        logger.debug('image_cache_name: %s', image_cache_name)

        return convert(input_filepath=image_cache_name, cleanup_files=False, size=size, zoom=zoom, rotation=rotation)

    def get_image(self, size=DISPLAY_SIZE, page=DEFAULT_PAGE_NUMBER, zoom=DEFAULT_ZOOM_LEVEL, rotation=DEFAULT_ROTATION, as_base64=False, version=None):
        if zoom < ZOOM_MIN_LEVEL:
            zoom = ZOOM_MIN_LEVEL

        if zoom > ZOOM_MAX_LEVEL:
            zoom = ZOOM_MAX_LEVEL

        rotation = rotation % 360

        file_path = self.get_valid_image(size=size, page=page, zoom=zoom, rotation=rotation, version=version)
        logger.debug('file_path: %s', file_path)

        if as_base64:
            mimetype = get_mimetype(open(file_path, 'r'), file_path, mimetype_only=True)[0]
            image = open(file_path, 'r')
            base64_data = base64.b64encode(image.read())
            image.close()
            return 'data:%s;base64,%s' % (mimetype, base64_data)
        else:
            return file_path

    def invalidate_cached_image(self, page):
        try:
            os.unlink(self.get_cached_image_name(page, self.latest_version.pk)[0])
        except OSError:
            pass

    def add_as_recent_document_for_user(self, user):
        RecentDocument.objects.add_document_for_user(user, self)
    """

    def delete(self, *args, **kwargs):
        for version in self.versions.all():
            version.delete()
        return super(Document, self).delete(*args, **kwargs)

    @property
    def size(self):
        return self.latest_version.size

    def new_version(self, file_object, user=None, comment=None):
        logger.debug('creating new document version')
        """
        # TODO: move this restriction to a signal processor of the checkouts app
        if not self.is_new_versions_allowed(user=user):
            raise NewDocumentVersionNotAllowed
        """

        new_version = DocumentVersion.objects.create(
            document=self,
            file=file_object,
            comment=comment or '',
        )

        logger.debug('new_version saved')

        # TODO: new HISTORY for version updates

        return new_version

    # Proxy methods
    def open(self, *args, **kwargs):
        """
        Return a file descriptor to a document's file irrespective of
        the storage backend
        """
        return self.latest_version.open(*args, **kwargs)

    def save_to_file(self, *args, **kwargs):
        return self.latest_version.save_to_file(*args, **kwargs)

    def exists(self):
        """
        Returns a boolean value that indicates if the document's
        latest version file exists in storage
        """
        return self.latest_version.exists()

    # Compatibility methods
    @property
    def file(self):
        return self.latest_version.file

    @property
    def file_mimetype(self):
        return self.latest_version.mimetype

    # TODO: rename to file_encoding
    @property
    def file_mime_encoding(self):
        return self.latest_version.encoding

    @property
    def date_updated(self):
        return self.latest_version.timestamp

    @property
    def checksum(self):
        return self.latest_version.checksum

    @property
    def signature_state(self):
        return self.latest_version.signature_state

    @property
    def pages(self):
        try:
            return self.latest_version.pages
        except AttributeError:
            # Document has no version yet
            return 0

    @property
    def page_count(self):
        return self.latest_version.page_count

    @property
    def latest_version(self):
        return self.versions.order_by('timestamp').last()

    """
    def document_save_to_temp_dir(self, filename, buffer_size=1024 * 1024):
        temporary_path = os.path.join(TEMPORARY_DIRECTORY, filename)
        return self.save_to_file(temporary_path, buffer_size)
    """

    @property
    def viewable(self):
        mimetype = self.file_mimetype
        # print mimetype
        if not mimetype:
            return False
        for mt in VIEWABLE_MIMETYPES:
            if mimetype.count(mt):
                return True
        if mimetype in ('application/zip', 'application/x-zip', 'application/x-zip-compressed'):
            f = self.open()
            is_content_package = ContentPackage().has_imsmanifest(file=f)
            f.close()
            return is_content_package
        return False

    @property
    def viewerjs_viewable(self):
        mimetype = self.file_mimetype
        for mt in VIEWERJS_MIMETYPES:
            if mimetype.count(mt):
                return True
        return False

# @python_2_unicode_compatible
class DocumentVersion(models.Model):
    """
    Model that describes a document version and its properties
    """
    _pre_open_hooks = {}
    _post_save_hooks = {}

    @classmethod
    def register_pre_open_hook(cls, order, func):
        cls._pre_open_hooks[order] = func

    @classmethod
    def register_post_save_hook(cls, order, func):
        cls._post_save_hooks[order] = func

    document = models.ForeignKey(Document, on_delete=models.CASCADE, verbose_name=_('Document'), related_name='versions')
    timestamp = models.DateTimeField(verbose_name=_('Timestamp'), auto_now_add=True)
    comment = models.TextField(blank=True, verbose_name=_('Comment'))

    # File related fields
    # file = models.FileField(upload_to=lambda instance, filename: UUID_FUNCTION(), storage=storage_backend, verbose_name=_('File'))
    # file = models.FileField(upload_to=lambda instance, filename: UUID_FUNCTION(), storage=storage_backend, verbose_name=_('File'), null=True, blank=True)
    file = models.FileField(storage=storage_backend, upload_to=UUID_FUNCTION, verbose_name=_('File'))
    mimetype = models.CharField(max_length=255, null=True, blank=True, editable=False)
    encoding = models.CharField(max_length=64, null=True, blank=True, editable=False)

    checksum = models.TextField(blank=True, null=True, verbose_name=_('Checksum'), editable=False)

    class Meta:
        verbose_name = _('Document version')
        verbose_name_plural = _('Document version')

    def __str__(self):
        return '{0} - {1}'.format(self.document, self.timestamp)

    def save(self, *args, **kwargs):
        """
        Overloaded save method that updates the document version's checksum,
        mimetype, page count and transformation when created
        """
        new_document_version = not self.pk

        # Only do this for new documents
        transformations = kwargs.pop('transformations', None)
        super(DocumentVersion, self).save(*args, **kwargs)

        for key in sorted(DocumentVersion._post_save_hooks):
            DocumentVersion._post_save_hooks[key](self)

        if new_document_version:
            # Only do this for new documents
            self.update_checksum(save=False)
            self.update_mimetype(save=False)
            self.save()
            # self.update_page_count(save=False)

            """
            if transformations:
                self.apply_default_transformations(transformations)

            post_version_upload.send(sender=self.__class__, instance=self)
            """

    def update_checksum(self, save=True):
        """
        Open a document version's file and update the checksum field using the
        user provided checksum function
        """
        if self.exists():
            source = self.open()
#           self.checksum = unicode(HASH_FUNCTION(source.read()))
            self.checksum = str(HASH_FUNCTION(source.read()))
            source.close()
            if save:
                self.save()

    """
    def update_page_count(self, save=True):
        handle, filepath = tempfile.mkstemp()
        # Just need the filepath, close the file description
        os.close(handle)

        self.save_to_file(filepath)
        try:
            detected_pages = get_page_count(filepath)
        except UnknownFileFormat:
            # If converter backend doesn't understand the format,
            # use 1 as the total page count
            detected_pages = 1
            self.description = ugettext('This document\'s file format is not known, the page count has therefore defaulted to 1.')
            self.save()
        try:
            os.remove(filepath)
        except OSError:
            pass

        current_pages = self.pages.order_by('page_number',)
        if current_pages.count() > detected_pages:
            for page in current_pages[detected_pages:]:
                page.delete()

        for page_number in range(detected_pages):
            DocumentPage.objects.get_or_create(
                document_version=self, page_number=page_number + 1)

        if save:
            self.save()

        return detected_pages

    # TODO: remove from here and move to converter app
    def apply_default_transformations(self, transformations):
        # Only apply default transformations on new documents
        if reduce(lambda x, y: x + y, [page.documentpagetransformation_set.count() for page in self.pages.all()]) == 0:
            for transformation in transformations:
                for document_page in self.pages.all():
                    page_transformation = DocumentPageTransformation(
                        document_page=document_page,
                        order=0,
                        transformation=transformation.get('transformation'),
                        arguments=transformation.get('arguments')
                    )

                    page_transformation.save()
    """

    def revert(self):
        """
        Delete the subsequent versions after this one
        """
        for version in self.document.versions.filter(timestamp__gt=self.timestamp):
            version.delete()

    def update_mimetype(self, save=True):
        """
        Read a document verions's file and determine the mimetype by calling the
        get_mimetype wrapper
        """
        if self.exists():
            try:
                self.mimetype, self.encoding = get_mimetype(self.open(), self.document.label)
            except:
                self.mimetype = ''
                self.encoding = ''
            finally:
                if save:
                    self.save()

    def delete(self, *args, **kwargs):
        self.file.storage.delete(self.file.path)
        return super(DocumentVersion, self).delete(*args, **kwargs)

    def exists(self):
        """
        Returns a boolean value that indicates if the document's file
        exists in storage
        """
        return self.file.storage.exists(self.file.path)

    def open(self, raw=False):
        """
        Return a file descriptor to a document version's file irrespective of
        the storage backend
        """
        if raw:
            return self.file.storage.open(self.file.path)
        else:
            result = self.file.storage.open(self.file.path)
            for key in sorted(DocumentVersion._pre_open_hooks):
                result = DocumentVersion._pre_open_hooks[key](result, self)

            return result

    def save_to_file(self, filepath, buffer_size=1024 * 1024):
        """
        Save a copy of the document from the document storage backend
        to the local filesystem
        """
        input_descriptor = self.open()
        output_descriptor = open(filepath, 'wb')
        while True:
            copy_buffer = input_descriptor.read(buffer_size)
            if copy_buffer:
                output_descriptor.write(copy_buffer)
            else:
                break

        output_descriptor.close()
        input_descriptor.close()
        return filepath

    @property
    def size(self):
        if self.exists():
            return self.file.storage.size(self.file.path)
        else:
            return None

    @property
    def page_count(self):
        return self.pages.count()

    """
    def get_page(self, page):
        if self.mimetype.lower().count('pdf'):
            i_stream = self.open()
            self.o_stream = StringIO()
            utils.get_pdf_page(i_stream, self.o_stream, page)
    """

    def get_pages(self, pageranges):
        if self.mimetype.lower().count('pdf'):
            i_stream = self.open()
            self.o_stream = StringIO()
            utils.get_pdf_pages(i_stream, self.o_stream, pageranges)

"""
from events.classes import Event

event_document_create = Event(name='documents_document_create', label=_('Document created'))
event_document_properties_edit = Event(name='documents_document_edit', label=_('Document properties edited'))
event_document_type_change = Event(name='documents_document_type_change', label=_('Document type changed'))

from django.dispatch import Signal

post_version_upload = Signal(providing_args=['instance'], use_caching=True)
post_document_type_change = Signal(providing_args=['instance'], use_caching=True)
"""
