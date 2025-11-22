"""
Centralized configuration for backend limits, validation rules,
and system behavior.

This file intentionally keeps everything in one place for simplicity,
without splitting into many small modules.
"""

import os
import sys
import re

# ---------------------------------------------------------
# SYSTEM PATH CONFIGURATION
# ---------------------------------------------------------

# Add project root (parent of 'backend') to Python path
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)

if PROJECT_ROOT not in sys.path:
    print(f"[config] Adding {PROJECT_ROOT} to sys.path")
    sys.path.insert(0, PROJECT_ROOT)
else:
    print(f"[config] {PROJECT_ROOT} already in sys.path")

# ---------------------------------------------------------
# CHAT VALIDATION LIMITS
# ---------------------------------------------------------

MAX_HINTS_LENGTH = 500                # max characters allowed in "hints"
MAX_QUESTION_LENGTH = 1000            # max characters allowed in "question"

# Disallowed invisible / control / bidi unicode characters
# Blocks:
#  - Zero-width chars
#  - Bidi override injections
#  - Control characters
UNSAFE_UNICODE_PATTERN = re.compile(
    r"[\u202A-\u202E\u2066-\u2069\u200B\u200C\u200D\uFEFF]"
    r"|[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]"
)

# ---------------------------------------------------------
# PDF & FILE PROCESSING LIMITS
# ---------------------------------------------------------

MAX_PAGES = 200                       # Maximum PDF pages allowed
MAX_TEXT_CHARS = 5_000_000            # Maximum extracted text allowed
MAX_PARSE_SECONDS = 10                # Timeout for PDF parsing

# ---------------------------------------------------------
# OTHER MISC SETTINGS (placeholder)
# ---------------------------------------------------------
