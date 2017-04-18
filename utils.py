
import os
if os.name == "nt":
    def symlink_ms(source, link_name):
        """ creates hard (?) symbolik link in Windows
        """
        import ctypes
        csl = ctypes.windll.kernel32.CreateSymbolicLinkW
        csl.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
        csl.restype = ctypes.c_ubyte
        flags = 1 if os.path.isdir(source) else 0
        try:
            if csl(link_name, source.replace('/', '\\'), flags) == 0:
                raise ctypes.WinError()
        except:
            pass
        os.symlink = symlink_ms

""" from commons - windows.log del 150720
from PyPDF2.pdf import *
reader = PdfFileReader("git.from.bottom.up.pdf")
reader.getNumPages()
page = reader.getPage(3)
writer = PdfFileWriter()
writer.addPage(page)
file = open("page3", "wb")
writer.write(file)
file.close
"""

from PyPDF2.pdf import PdfFileReader, PdfFileWriter

def make_pdf_writer():
    return PdfFileWriter()

def get_pdf_page(i_stream, o_stream, page):
    """ return ...
    """ 
    from PyPDF2.pdf import PdfFileReader, PdfFileWriter
    reader = PdfFileReader(i_stream)
    if page > reader.getNumPages():
        return None
    writer = PdfFileWriter()
    page = reader.getPage(page)
    writer.addPage(page)
    writer.write(o_stream)

def write_pdf_pages(i_stream, writer, ranges):
    """ append to the writer pages from the source PDF stream in the range specified
        range is a list of 2 elements: [low, high]
    """ 
    reader = PdfFileReader(i_stream)
    n_pages = reader.getNumPages()
    if ranges:
        for r in ranges:
            if not isinstance(r, (list, tuple)):
                continue
            if len(r) < 1 or len(r) > 2:
                raise 'invalid page range'
            low = r[0]
            if not isinstance(low, int) or low < 1 or low > n_pages:
                raise 'invalid page range'
            high = low
            p = low - 1
            if len(r) == 2:
                high = r[1]
                if not isinstance(high, int) or high < low or high > n_pages:
                    raise 'invalid page range'
            while p < high:
                writer.addPage(reader.getPage(p))
                p += 1
    else:
        writer.appendPagesFromReader(reader)

empty_words = ('and', 'the', 'not', 'non',)

def filter_empty_words(text):
    for word in empty_words:
        text = text.replace(' %s ' % word, ' ')
    return text

from lxml import html
TO_DROP_TAGS = [
    'link', 'script', 'style','iframe',
]
BLOCK_TAGS = [
   'body', 'header', 'hgroup', 'main',  'aside', 'footer',
   'address', 'article', 'field', 'section', 'nav',
   'div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'dl', 'dt', 'dd',
   'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',
   'a', 'blockquote', 'pre', 'noscript',
   'img', 'figure', 'figcaption', 'canvas', 'video',
   'form', 'fieldset', 'input', 'button', 'select', 'option', 'textarea', 'output',
]
# http://stackoverflow.com/questions/4624062/get-all-text-inside-a-tag-in-lxml
# from wip.utils
def strings_from_block(block):
    block_children = [child for child in block.getchildren() if child.tag in BLOCK_TAGS]
    if block_children:
        text = block.text
        if text: text = text.strip()
        if text: yield text
        for child in block_children:
            for el in strings_from_block(child):
                yield el
        tail = block.tail
        if tail: tail = tail.strip()
        if tail: yield tail
    else:
        content = block.text_content()
        if content: content = content.strip()
        if content: yield content

# from wip.utils
def strings_from_html(string, fragment=False):
    doc = html.fromstring(string)
    if fragment:
        body = doc
    else:
        body = doc.find('body')
    for tag in TO_DROP_TAGS:
        els = body.findall(tag)
        for el in els:
            el.getparent().remove(el) 
    for s in strings_from_block(body):
        if s:
            yield s

"""
see http://stackoverflow.com/questions/843392/python-get-http-headers-from-urllib2-urlopen-call
    Python: Get HTTP headers from urllib2.urlopen call?
"""
from django.utils.translation import ugettext_lazy as _, string_concat
from django.utils.text import capfirst

import urllib2
""" a Request using the HEAD method in place of the default one (GET or PUT) """
class HeadRequest(urllib2.Request):
    def get_method(self):
        return "HEAD"
def get_headers(url):
    """ tries to open the resource at the given url;
        returns the HTTP headers as a dict or a dict including only the exception object """
    request = HeadRequest(url)
    try:
        response = urllib2.urlopen(request)
        response_headers = response.info()
        return response_headers.dict
    except Exception as e:
        return { 'error': e}

def x_frame_protection(url):
    """ returns an empty string if the resource at the given url can be loaded inside an i-frame;
        otherways returns a localized error message """
    headers = get_headers(url)
    """
    e = headers.get('error', None)
    if e:
        return string_concat(capfirst(_('a problem was found in accessing this resource')), '. ', capfirst(_('the following error code was returned')), ': ', str(e))
    """
    x_frame_options = headers.get('x-frame-options', '')
    # if x_frame_options and x_frame_options.upper() == 'SAMEORIGIN':
    if x_frame_options:
        return string_concat(capfirst(_('embedding inside a page the view of this resource is forbidden: please, use the link above to access it directly')), '. ')
    return ''
