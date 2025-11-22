import os
import threading

from contextlib import contextmanager
from pypdf import PdfReader   # Secure maintained fork of PyPDF2
from werkzeug.datastructures import FileStorage

from backend.configs.config import MAX_PAGES, MAX_TEXT_CHARS, MAX_PARSE_SECONDS

class TimeoutException(Exception):
    pass

@contextmanager
def time_limit(seconds):
    def timer():
        raise_timeout()

    def raise_timeout():
        raise TimeoutException("[time_limit] PDF parsing exceeded safe time limit")

    # Create a timer thread that raises the exception after N seconds
    timer_thread = threading.Timer(seconds, raise_timeout)
    timer_thread.start()

    try:
        yield
    finally:
        timer_thread.cancel()


def extract_text_secure(file: FileStorage, max_size_mb=None) -> str:
    print("[extract_text_secure] Starting secure PDF extraction")

    max_size_mb = max_size_mb or int(os.environ.get("MAX_PDF_SIZE_MB"))
    max_bytes = max_size_mb * 1024 * 1024

    print(f"[extract_text_secure] Max allowed size: {max_size_mb} MB")

    size = getattr(file, "content_length", None)

    if size:
        print(f"[extract_text_secure] Uploaded file size: {size} bytes")

    # If size known, enforce size limit
    if size and size > max_bytes:
        raise ValueError(f"[extract_text_secure] PDF too large ({size} bytes). Limit is {max_bytes} bytes.")

    try:
        with time_limit(MAX_PARSE_SECONDS):
            print("[extract_text_secure] Parsing PDF with pypdf...")

            pdf = PdfReader(file.stream)

            if pdf.is_encrypted:
                print("[extract_text_secure] PDF is encrypted; attempting decryption...")
                if not pdf.decrypt(""):
                    raise ValueError("[extract_text_secure] Encrypted PDF cannot be processed")
                print("[extract_text_secure] Successfully decrypted PDF")

            num_pages = len(pdf.pages)
            print(f"[extract_text_secure] PDF contains {num_pages} pages")

            if num_pages > MAX_PAGES:
                raise ValueError(f"[extract_text_secure] PDF has too many pages ({num_pages}). Limit is {MAX_PAGES}.")

            parts = []
            total_chars = 0

            for idx, page in enumerate(pdf.pages):
                print(f"[extract_text_secure] Extracting text from page {idx+1}/{num_pages}")
                try:
                    txt = page.extract_text() or ""
                except Exception as e:
                    print(f"[extract_text_secure] Failed to extract text from page {idx+1}: {e}")
                    continue

                parts.append(txt)
                total_chars += len(txt)

                print(f"[extract_text_secure] Page {idx+1} extracted: {len(txt)} chars (total so far: {total_chars})")

                if total_chars > MAX_TEXT_CHARS:
                    raise ValueError("[extract_text_secure] Extracted text exceeds maximum safe length")

            text = "".join(parts)
            if not text:
                raise ValueError("[extract_text_secure] No extractable text found in PDF")

            print(f"[extract_text_secure] Successfully extracted {len(text)} characters from PDF")
            return text

    except TimeoutException as e:
        raise RuntimeError(f"[extract_text_secure] PDF processing timed out: {e}")
    except Exception as e:
        raise RuntimeError(f"[extract_text_secure] PDF parsing failed: {e}")



def allowed_file(filename):
    """Check if file extension is allowed"""
    # Configuration constants
    ALLOWED_EXTENSIONS = {'pdf'}

    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS