
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

def get_pdf_pages(i_stream, o_stream, pageranges):
    """ return or write an output stream with pages from the source PDF stream in range specified
    range is a list of elements:
    - int elements represent individual pages; numbering starts from 1
    - sequences of 2 elements [low, high] represent a page range
    """ 
    from PyPDF2.pdf import PdfFileReader, PdfFileWriter
    reader = PdfFileReader(i_stream)
    n_pages = reader.getNumPages()
    writer = PdfFileWriter()
    for pr in pageranges:
        if isinstance(pr, int):
            page = reader.getPage(pr)
            writer.addPage(page-1)
            writer.write(o_stream)
        elif isinstance(pr, (list, tuple)) and len(pr)==2:
            low = pr[0]
            high = pr[1]
            if not isinstance(low, int) or low<1 or low>n_pages:
                raise 'invalid page range'
            if not isinstance(high, int) or high<low or high>n_pages:
                raise 'invalid page range'
            p = low-1
            step = 1
            while p < high:
                page = reader.getPage(p)
                writer.addPage(page)
                p += step
            writer.write(o_stream)
        else:
            raise 'invalid page range'

    file = open("page3", "wb")
    writer.write(file)
    file.close

empty_words = ('and', 'the',)

def filter_empty_words(text):
    for word in empty_words:
        text = text.replace(' %s ' % word, ' ')
