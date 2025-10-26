from PyPDF2 import PdfReader
from werkzeug.datastructures import FileStorage

def extract_text_from_pdf_pypdf2(file: FileStorage):
    with file.stream as file_stream:
        pdf_reader = PdfReader(file_stream)
        text = ""
        for page_number in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_number].extract_text()
    # test print the first 100 characters
    print(text[:100])
    return text



def allowed_file(filename):
    """Check if file extension is allowed"""

    # Configuration constants
    ALLOWED_EXTENSIONS = {'pdf'}

    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS