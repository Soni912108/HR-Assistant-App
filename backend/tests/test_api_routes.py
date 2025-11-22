import os
import sys
from io import BytesIO
import requests
import re
# third-party modules
import dotenv
import pytest
from reportlab.pdfgen import canvas
from pypdf import PdfWriter

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

dotenv.load_dotenv()

BASE_URL_TEST = os.getenv("BASE_URL_TEST", "http://localhost:5000")
TEST_EMAIL = os.getenv("TEST_EMAIL")
TEST_PASSWORD = os.getenv("TEST_PASSWORD") 


# -----------------------------
# Helper functions to generate PDFs
# -----------------------------
def create_valid_extractable_pdf():
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "This is a test PDF")

    pdf_bytes = pdf.output(dest="S").encode("latin1")
    
    buf = BytesIO(pdf_bytes)
    return buf

def create_encrypted_pdf():
    """Generate an encrypted PDF."""
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)

    buffer = BytesIO()
    writer.encrypt("password123")
    writer.write(buffer)
    buffer.seek(0)
    return buffer.read()


def create_corrupted_pdf():
    """Bytes that start like a PDF but are corrupted."""
    return b"%PDF-1.7 corrupted_content %%EOF"


def create_empty_pdf():
    """Empty bytes → should trigger your 'empty file' validation."""
    return b""


def create_image_only_pdf():
    """A PDF with an embedded image (no extractable text)."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawImage("backend/tests/sample.png", 50, 600, width=200, height=200)
    c.save()
    buffer.seek(0)
    return buffer.read()


def create_large_pdf(min_mb=21):
    """PDF exceeding max_size_mb=20MB."""
    return b"%PDF-1.4\n" + (b"0" * (min_mb * 1024 * 1024))


class TestUploadWorkflow:

    def _success(self, message: str):
        print(f"[SUCCESS] {message}")

    @pytest.fixture(scope="class")
    def login_session(self):
        s = requests.Session()
        resp = s.post(f"{BASE_URL_TEST}/login", data={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert resp.status_code == 200
        self._success("Logged in successfully.")
        return s

    @pytest.fixture(scope="class")
    def conversation_id(self, login_session):
        resp = login_session.get(f"{BASE_URL_TEST}/app/dashboard")
        assert resp.status_code == 200

        pattern = re.compile(r'data-conversation-id=["\'](?P<cid>\d+)["\']')
        matches = pattern.findall(resp.text)
        assert len(matches) > 0

        self._success("Fetched valid conversation ID from dashboard.")
        return matches[0]

    # -------------------------------------------------------------------------
    # 1) VALID PDF UPLOAD
    # -------------------------------------------------------------------------
    def test_valid_pdf_upload(self, login_session, conversation_id):
        pdf = create_valid_extractable_pdf()

        resp = login_session.post(
            f"{BASE_URL_TEST}/app/upload",
            files={"files": ("test.pdf", pdf, "application/pdf")},
            data={"conversation_id": conversation_id}
        )

        assert resp.status_code == 200
        assert "success" in resp.json().get("status", "").lower()
        self._success("Valid PDF upload passed — extractable PDF processed successfully.")

    # -------------------------------------------------------------------------
    # 2) EMPTY PDF
    # -------------------------------------------------------------------------
    def test_empty_pdf_rejected(self, login_session, conversation_id):
        pdf = create_empty_pdf()

        resp = login_session.post(
            f"{BASE_URL_TEST}/app/upload",
            files={"files": ("empty.pdf", pdf, "application/pdf")},
            data={"conversation_id": conversation_id}
        )

        assert resp.status_code in (400, 500)
        assert "cannot read an empty file" in resp.json().get("message", "").lower()
        self._success("Empty PDF correctly rejected by backend.")

    # -------------------------------------------------------------------------
    # 3) LARGE PDF
    # -------------------------------------------------------------------------
    def test_large_pdf_rejected(self, login_session, conversation_id):
        large_pdf = create_large_pdf()

        resp = login_session.post(
            f"{BASE_URL_TEST}/app/upload",
            files={"files": ("large.pdf", large_pdf, "application/pdf")},
            data={"conversation_id": conversation_id}
        )

        assert resp.status_code in (400, 500)
        assert "too large" in resp.text.lower()
        self._success("Large PDF correctly rejected for exceeding size limits.")

    # -------------------------------------------------------------------------
    # 4) ENCRYPTED PDF
    # -------------------------------------------------------------------------
    def test_encrypted_pdf_rejected(self, login_session, conversation_id):
        encrypted = create_encrypted_pdf()

        resp = login_session.post(
            f"{BASE_URL_TEST}/app/upload",
            files={"files": ("encrypted.pdf", encrypted, "application/pdf")},
            data={"conversation_id": conversation_id}
        )

        assert resp.status_code in (400, 500)
        assert "encrypted" in resp.json().get("message", "").lower()
        self._success("Encrypted PDF correctly rejected — backend detected encryption.")

    # -------------------------------------------------------------------------
    # 5) CORRUPTED PDF
    # -------------------------------------------------------------------------
    def test_corrupted_pdf_rejected(self, login_session, conversation_id):
        corrupted = create_corrupted_pdf()

        resp = login_session.post(
            f"{BASE_URL_TEST}/app/upload",
            files={"files": ("corrupted.pdf", corrupted, "application/pdf")},
            data={"conversation_id": conversation_id}
        )

        assert resp.status_code == 500
        assert "stream has ended unexpectedly" in resp.json().get("message", "").lower()
        self._success("Corrupted PDF correctly rejected — parsing failure detected.")

    # -------------------------------------------------------------------------
    # 6) NO extractable text
    # -------------------------------------------------------------------------
    def test_pdf_no_extractable_text(self, login_session, conversation_id):
        pdf = create_image_only_pdf()

        resp = login_session.post(
            f"{BASE_URL_TEST}/app/upload",
            files={"files": ("image_only.pdf", pdf, "application/pdf")},
            data={"conversation_id": conversation_id}
        )

        assert resp.status_code == 500
        assert "no extractable text" in resp.json().get("message", "").lower()
        self._success("Image-only PDF rejected — no extractable text found.")

    # -------------------------------------------------------------------------
    # 7) NON-PDF FILE
    # -------------------------------------------------------------------------
    def test_non_pdf_file_rejected(self, login_session, conversation_id):
        fake = b"This is not a PDF."

        resp = login_session.post(
            f"{BASE_URL_TEST}/app/upload",
            files={"files": ("file.txt", fake, "text/plain")},
            data={"conversation_id": conversation_id}
        )

        assert resp.status_code == 400
        assert "is not a pdf" in resp.json().get("message", "").lower()
        self._success("Non-PDF file correctly rejected with proper error message.")

    # -------------------------------------------------------------------------
    # 8) MULTIPLE FILE UPLOAD
    # -------------------------------------------------------------------------
    def test_multiple_file_upload(self, login_session, conversation_id):
        pdf1 = create_valid_extractable_pdf()
        pdf2 = create_valid_extractable_pdf()

        resp = login_session.post(
            f"{BASE_URL_TEST}/app/upload",
            files=[
                ("files", ("one.pdf", pdf1, "application/pdf")),
                ("files", ("two.pdf", pdf2, "application/pdf")),
            ],
            data={"conversation_id": conversation_id}
        )

        assert resp.status_code == 400
        assert "single file upload is supported" in resp.json().get("message", "").lower()
        self._success("Multiple-file upload correctly rejected — single-file policy enforced.")

    # -------------------------------------------------------------------------
    # 9) MISSING CONVERSATION ID
    # -------------------------------------------------------------------------
    def test_missing_conversation_id(self, login_session):
        pdf = create_valid_extractable_pdf()

        resp = login_session.post(
            f"{BASE_URL_TEST}/app/upload",
            files={"files": ("test.pdf", pdf, "application/pdf")}
        )

        assert resp.status_code == 500
        assert "missing conversation id" in resp.json().get("message", "").lower()
        self._success("Upload without conversation ID correctly rejected.")

    # -------------------------------------------------------------------------
    # 10) CONVERSATION NOT FOUND
    # -------------------------------------------------------------------------
    def test_invalid_conversation_id(self, login_session):
        pdf = create_valid_extractable_pdf()

        resp = login_session.post(
            f"{BASE_URL_TEST}/app/upload",
            files={"files": ("test.pdf", pdf, "application/pdf")},
            data={"conversation_id": 999999999}
        )

        assert resp.status_code == 404
        assert "not found" in resp.text.lower()
        self._success("Invalid conversation ID correctly rejected with 404.")

