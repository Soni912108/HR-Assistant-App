from PyPDF2 import PdfReader
from werkzeug.datastructures import FileStorage

def extract_text_from_pdf_pypdf2(file: FileStorage):
    with file.stream as file_stream:
        pdf_reader = PdfReader(file_stream)
        text = ""
        for page_number in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_number].extract_text()
    return text



