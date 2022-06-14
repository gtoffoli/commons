# -*- coding: utf-8 -*-"""

# Python 2 - Python 3 compatibility
from six import BytesIO
import urllib.request as urllib2

import os

from pikepdf import Pdf, OutlineItem

def tree_to_list(tree):
    list = [tree[0]]
    for child in tree[1]:
        list = list + tree_to_list(child)
    return list

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

import random
import string
from datetime import datetime, timezone

# def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits, date_seed=False, prefix=''):
    if date_seed:
        date = datetime.now(timezone.utc).date()
        int_date = date.day + date.month * 32 # unique id for day in year
        random.seed(int_date)
    random_string = ''.join(random.choice(chars) for _ in range(size))
    return prefix + random_string

# from PyPDF2.pdf import PdfFileReader, PdfFileWriter
from weasyprint import HTML, CSS

try:
    import nbformat
    from nbconvert import HTMLExporter, PDFExporter
except:
    pass

def text_to_html(text):
    return text.replace('\n', '<br>')

def make_pdf_writer():
    # return PdfFileWriter()
    return Pdf.new()

def pdf_get_numpages(pdf):
    # return pdf.getNumPages()
    return len(pdf.pages)

def pdf_add_bookmark(writer, s, p):
    with writer.open_outline() as outline:
        outline.root.extend([OutlineItem(s, p)])

def pdf_writer_save(writer, stream):
    writer.save(stream)

def ipynb_to_html(data):
    try:
        data = data.decode()
    except:
        pass
    notebook = nbformat.reads(data, as_version=4)
    html_exporter = HTMLExporter()
    body, resources = html_exporter.from_notebook_node(notebook)
    return body

def ipynb_url_to_html(url):
    data = urllib2.urlopen(url).read()
    return ipynb_to_html(data)

def document_to_writer(document, writer, ranges=None, mimetype='application/pdf'):
    if mimetype=='application/x-ipynb+json':
        f = document.open()
        data = f.read()
        f.close
        notebook = nbformat.reads(data, as_version=4)
        pdf_exporter = PDFExporter()
        pdf_data, resources = pdf_exporter.from_notebook_node(notebook)
        i_stream = BytesIO(pdf_data)
    else:
        return
    return write_pdf_pages(i_stream, writer, ranges=ranges)

def url_to_writer(url, writer, ranges=None, mimetype='text/html'):
    if mimetype=='text/html':
        i_stream = BytesIO()
        stylesheets = [CSS(string='@page { size: A4 landscape; }')]
        HTML(url=url).write_pdf(i_stream, stylesheets=stylesheets)
    elif mimetype=='application/x-ipynb+json':
        response = urllib2.urlopen(url).read().decode()
        notebook = nbformat.reads(response, as_version=4)
        pdf_exporter = PDFExporter()
        pdf_data, resources = pdf_exporter.from_notebook_node(notebook)
        i_stream = BytesIO(pdf_data)
    else:
        return 0
    return write_pdf_pages(i_stream, writer, ranges=ranges)

def html_to_writer(html, writer, css=None, ranges=None, landscape=False):
    stylesheets = landscape and [CSS(string='@page { size: A4 landscape; }')] or None
    i_stream = BytesIO()
    """
    stylesheet = CSS(string='body { font-family: Arial; } a { text-decoration: none; };')
    HTML(string=html).write_pdf(i_stream, stylesheets=[stylesheet])
    
    if css is None:
        css = 'body { font-family: Arial; };'
    stylesheets = css and [CSS(string=css)] or None
    HTML(string=html).write_pdf(i_stream, stylesheets=stylesheets)
    """
    HTML(string=html).write_pdf(target=i_stream, stylesheets=stylesheets)
    return write_pdf_pages(i_stream, writer, ranges=ranges)

def write_pdf_pages(i_stream, writer, ranges=None):
    """ append to the writer pages from the source PDF stream in the range specified
        range is a list of 2 elements: [low, high]
    """ 
    # reader = PdfFileReader(i_stream, strict=False)
    reader = Pdf.open(i_stream)
    # n_pages = reader.getNumPages()
    n_pages = len(reader.pages)
    if ranges:
        for r in ranges:
            if not isinstance(r, (list, tuple)):
                continue
            if len(r) > 2:
                # raise 'invalid page range'
                continue
            elif r:
                low = r[0]
                high = low
            else: # empty range
                low = 1
                high = n_pages
            if not isinstance(low, int) or low < 1 or low > n_pages:
                # raise 'invalid page range'
                continue
            p = low - 1
            if len(r) == 2:
                high = r[1]
                if not isinstance(high, int) or high < low:
                    # raise 'invalid page range'
                    continue
            while p < high and p < n_pages:
                # writer.addPage(reader.getPage(p))
                writer.pages.append(reader.pages[p])
                p += 1
    else:
        # writer.appendPagesFromReader(reader)
        writer.pages.extend(reader.pages)
    return n_pages

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
from django.utils.translation import gettext_lazy as _
from django.utils.text import capfirst
from django.conf import settings
from django.utils.text import format_lazy
def string_concat(*strings):
    return format_lazy('{}' * len(strings), *strings)

""" a Request using the HEAD method in place of the default one (GET or PUT) """
class HeadRequest(urllib2.Request):
    def get_method(self):
        return "HEAD"
def get_request_headers(url):
    """ tries to open the resource at the given url;
        returns the HTTP headers as a dict or a dict including only the exception object """
    try:
        request = HeadRequest(url) # 190114 GT: moved this line inside try branch
        response = urllib2.urlopen(request)
        response_headers = response.info()
        return response_headers
    except Exception as e:
        return { 'error': e}

def get_request_content(url):
    try:
        request = urllib2.Request(url) # 190114 GT: moved this line inside try branch
        response = urllib2.urlopen(request)
        if response.getcode() in [200]:
            return response.read()
    except:
        pass
    return None

def x_frame_protection(url):
    """ returns an empty string if the resource at the given url can be loaded inside an i-frame;
        otherways returns a localized error message """
    headers = get_request_headers(url)
    x_frame_options = headers.get('x-frame-options', '')
    # if x_frame_options and x_frame_options.upper() == 'SAMEORIGIN':
    if x_frame_options:
        return string_concat(capfirst(_('embedding inside a page the view of this resource is forbidden: please, use the link above to access it directly')), '. ')
    return ''
