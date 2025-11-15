import os
import sys
# make project root (parent of 'backend') available on sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
if project_root not in sys.path:
    print(f"Adding {project_root} to sys.path")
    sys.path.insert(0, project_root)
else:
    print(f"{project_root} already in sys.path. Continuing...")


import io
import pytest
from werkzeug.datastructures import FileStorage
from backend.utils.file_utils import extract_text_from_pdf_pypdf2

# Helper: create a minimal valid PDF in memory
def make_pdf_bytes(text="Hello"):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(100, 750, text)
    c.save()
    buf.seek(0)
    return buf.read()

def test_empty_file_raises():
    file = FileStorage(stream=io.BytesIO(b""), filename="empty.pdf", content_length=0)
    with pytest.raises(ValueError, match="empty"):
        extract_text_from_pdf_pypdf2(file)

def test_too_large_file_raises():
    big_bytes = b"0" * (21 * 1024 * 1024)  # 21MB
    file = FileStorage(stream=io.BytesIO(big_bytes), filename="big.pdf", content_length=len(big_bytes))
    with pytest.raises(ValueError, match="too large"):
        extract_text_from_pdf_pypdf2(file, max_size_mb=20)

def test_valid_pdf_extracts_text():
    pdf_bytes = make_pdf_bytes("Test PDF")
    file = FileStorage(stream=io.BytesIO(pdf_bytes), filename="test.pdf", content_length=len(pdf_bytes))
    text = extract_text_from_pdf_pypdf2(file)
    assert "Test PDF" in text

def test_corrupted_pdf_raises():
    file = FileStorage(stream=io.BytesIO(b"%PDF-1.4 corrupted content"), filename="corrupt.pdf", content_length=25)
    with pytest.raises(RuntimeError, match="Failed to parse PDF"):
        extract_text_from_pdf_pypdf2(file)

def test_encrypted_pdf_raises():
    # Create a password-protected PDF (requires PyPDF2)
    from PyPDF2 import PdfWriter
    buf = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.encrypt("secret")
    writer.write(buf)
    buf.seek(0)
    file = FileStorage(stream=io.BytesIO(buf.read()), filename="encrypted.pdf")
    with pytest.raises(ValueError, match="encrypted"):
        extract_text_from_pdf_pypdf2(file)

def test_pdf_with_no_text_raises():
    # Create a PDF with a blank page (no extractable text)
    from PyPDF2 import PdfWriter
    buf = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(buf)
    buf.seek(0)
    file = FileStorage(stream=io.BytesIO(buf.read()), filename="blank.pdf")
    with pytest.raises(ValueError, match="No extractable text"):
        extract_text_from_pdf_pypdf2(file)


def test_allowed_file_name_with_extension():
    from backend.utils.file_utils import allowed_file
    assert allowed_file("document.pdf") is True
    assert allowed_file("image.png") is False
    assert allowed_file("report.PDF") is True
    assert allowed_file("no_extension") is False