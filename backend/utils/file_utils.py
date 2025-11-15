from PyPDF2 import PdfReader
from werkzeug.datastructures import FileStorage
import os
from typing import Optional

def extract_text_from_pdf_pypdf2(file: FileStorage, max_size_mb: Optional[int] = None) -> str:
    """
    Extract text from an uploaded PDF with size checks and clear error messages.

    Raises:
        ValueError: for validation errors (empty file, too large, etc).
        RuntimeError: for PDF parsing/extraction errors.
    """
    # Configurable maximum (MB). Can be overridden via env var MAX_PDF_SIZE_MB or the max_size_mb arg.
    DEFAULT_MAX_MB = 20
    if max_size_mb is None:
        try:
            max_size_mb = int(os.environ.get("MAX_PDF_SIZE_MB", DEFAULT_MAX_MB))
        except Exception:
            max_size_mb = DEFAULT_MAX_MB
    max_bytes = max_size_mb * 1024 * 1024

    # Try to get content length from FileStorage if available
    size = getattr(file, "content_length", None)

    # If not available, attempt to determine by seeking the stream (if possible)
    if size is None:
        stream = file.stream
        try:
            current_pos = stream.tell()
            stream.seek(0, os.SEEK_END)
            size = stream.tell()
            stream.seek(current_pos)
        except (OSError, AttributeError):
            size = None  # couldn't determine size

    if size == 0:
        raise ValueError("Uploaded PDF is empty.")

    if size is not None and size > max_bytes:
        raise ValueError(f"Uploaded PDF is too large ({size / (1024*1024):.1f} MB). Maximum allowed is {max_size_mb} MB.")

    if size is None:
        # Warn but allow: size couldn't be determined; this is less safe for very large files
        print("[extract_text_from_pdf_pypdf2]: Warning - could not determine uploaded file size; proceeding with extraction.")

    try:
        # Read pages and accumulate text efficiently
        with file.stream as file_stream:
            pdf_reader = PdfReader(file_stream)
            if pdf_reader.is_encrypted:
                try:
                    pdf_reader.decrypt("")  # Try to decrypt with empty password
                except Exception:
                    raise ValueError("The PDF is encrypted and cannot be processed.")
            parts = []
            for page in pdf_reader.pages:
                try:
                    page_text = page.extract_text()
                except Exception as e:
                    print(f"[extract_text_from_pdf_pypdf2]: Failed to extract text from a page: {e}")
                    continue  # Skip problematic pages
                if page_text:
                    parts.append(page_text)
            text = "".join(parts)
    except Exception as e:
        # Provide a clear error for the caller to surface to the user
        raise RuntimeError(f"Failed to parse PDF: {e}")

    if not text:
        # No text extracted (could be scanned images, encrypted, or empty)
        raise ValueError("No extractable text found in the PDF. The file may be scanned/images or encrypted.")

    print(f"[extract_text_from_pdf_pypdf2]: Extracted {len(text)} characters from PDF.")
    return text



def allowed_file(filename):
    """Check if file extension is allowed"""

    # Configuration constants
    ALLOWED_EXTENSIONS = {'pdf'}

    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS