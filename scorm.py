# -*- coding: utf-8 -*-"""

import os
import stat
import shutil
import re
import time
import xml.etree.ElementTree as ET
import zipfile

from django.template.defaultfilters import slugify
from django.conf import settings

class ContentPackage(object):

    def __init__(self, fpath=None, dpath=None, file=None, slug=None):
        self.fpath = fpath # path of the zip file
        self.dpath = dpath # path of the directory for uncompressed package
        self.file = file # handle to open zip file
        self.slug = slug # safe name to be used to build the directory path

    def has_imsmanifest(self, fpath=None, file=None):
        if not file:
            self.fpath = fpath or self.fpath
            if os.path.isfile(self.fpath):
                file = open(self.fpath, "rb")
        if file:
            zf = zipfile.ZipFile(file)
            for n in zf.namelist():
                if n == 'imsmanifest.xml':
                    return True
        return False

    def read(self, fpath=None, dpath=None):
        self.fpath = fpath or self.fpath
        self.dpath = dpath or self.dpath
        self.version_scorm = None
        self.index_page = None
        
        if (self.file and self.slug) or os.path.isfile(self.fpath):
            if self.file and self.slug:
                f = self.file
                slug = self.slug
            else:
                head, tail = os.path.split(fpath)
                name, ext = os.path.splitext(tail)
                if not ext=='.zip':
                    return {'error': 'no zip extension'}
                slug = slugify(name)
                f = open(self.fpath, "rb")
            if not zipfile.is_zipfile(f):
                return {'error': 'no zip file'}
            if not self.dpath:
                self.dpath = os.path.join(settings.SCORM_ROOT, slug)
            dstat = None
            if os.path.isdir(self.dpath):
                dstat = os.stat(self.dpath)
                dtime = dstat[stat.ST_MTIME]
                dage = time.time() - dtime
                if dage > settings.SCORM_EXPIRATION:
                    # print ('directory expired')
                    shutil.rmtree(self.dpath, ignore_errors=True)
                    dstat = None
            if not dstat:
                # print ('extracting', self.fpath, 'to', self.dpath)
                zf = zipfile.ZipFile(f)
                zf.extractall(self.dpath)

            try:
                tree = ET.parse('{}/imsmanifest.xml'.format(self.dpath))
            except IOError:
                return {'error': 'manifest IO'}
            else:
                namespace = ''
                for node in [node for _, node in ET.iterparse('{}/imsmanifest.xml'.format(self.dpath), events=['start-ns'])]:
                    if node[0] == '':
                        namespace = node[1]
                        break
                root = tree.getroot()
                if namespace:
                    resource = root.find('{{{0}}}resources/{{{0}}}resource'.format(namespace))
                    schemaversion = root.find('{{{0}}}metadata/{{{0}}}schemaversion'.format(namespace))
                else:
                    resource = root.find('resources/resource')
                    schemaversion = root.find('metadata/schemaversion')
                if os.path.isfile('{}/story_html5.html'.format(self.dpath)):
                    self.index_page = 'story_html5.html'
                elif os.path.isfile('{}/story.html'.format(self.dpath)):
                    self.index_page = 'story.html'
                elif len(resource):
                    self.index_page = resource.get('href')
                if (schemaversion is not None) and (re.match('^1.2$', schemaversion.text) is None):
                    self.version_scorm = 'SCORM_2004'
                else:
                    self.version_scorm = 'SCORM_12'
                self.url = '%s/%s/%s' % (settings.SCORM_URL, self.slug, self.index_page)

            return {'version': self.version_scorm, 'dpath': self.dpath, 'index': self.index_page, 'url': self.url}
