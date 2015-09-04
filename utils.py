
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
    for pr in pageranges:
        writer = PdfFileWriter()
        if isinstance(pr, int):
            page = reader.getPage(pr)
            writer.addPage(page)
            writer.write(o_stream)
        elif isinstance(pr, (list, tuple)) and len(pr)==2:
            low = pr[0]
            high = pr[1]
            if not isinstance(low, int) or low<1 or low>n_pages:
                raise 'invalid page range'
            if not isinstance(high, int) or high<low or high>n_pages:
                raise 'invalid page range'
            p = low
            step = 1
            while p <= high:
                page = reader.getPage(p)
                writer.addPage(page)
                p += step
            writer.write(o_stream)
        else:
            raise 'invalid page range'

    file = open("page3", "wb")
    writer.write(file)
    file.close
            