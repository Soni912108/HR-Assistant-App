# builtin modules
import re
from typing import Optional, Union, Tuple
# local modules
from .file_utils import allowed_file
# third-party modules
from flask import Response, render_template, flash, redirect, request


# Error handling and redirection
def handle_errors_and_redirect(
    error_message: str,
    category: str = 'danger',
    redirect_url: Optional[str] = None
) -> Union[Response, render_template]:
    """
    A function to handle errors and redirect the user.
    
    Note: This function assumes that flash() and redirect() are available 
    in the calling context/module.

    Parameters
    ----------
    error_message : str
        The error message to be displayed to the user.
    category : str, optional
        The category of the error message, by default 'danger'.
    redirect_url : Optional[str], optional
        The URL to redirect the user to, by default None.

    Returns
    -------
    Union[Response, render_template]
        A Response or render_template object, depending on whether a redirect URL was provided.
    """
    flash(error_message, category)
    return redirect(redirect_url) if redirect_url else render_template(request.endpoint.split('.')[-1] + '.html')

# Registration data validation
def validate_registration_data(
        email: str, 
        username: str, 
        password: str, 
        confirm_password: str
    ) -> Tuple[bool, Optional[str]]:
    """
    Validates registration form data.
    
    Parameters
    ----------
    email : str
        User's email address
    username : str
        User's username
    password : str
        User's password
    confirm_password : str
        Password confirmation
    
    Returns
    -------
    Tuple[bool, Optional[str]]
        A tuple containing (is_valid, error_message)
        If is_valid is True, error_message will be None
        If is_valid is False, error_message will contain the validation error
    """
    # Check if all fields are provided
    if not all([email, username, password, confirm_password]):
        return False, 'Please fill in all fields'
    
    # Validate email format
    if not is_valid_email(email):
        return False, 'Please enter a valid email address'
    
    # Validate username length
    if len(username) < 10:
        return False, 'Username must be at least 10 characters long'
    
    if len(username) > 20:
        return False, 'Username must be less than 20 characters long'
    
    # Validate password length
    if not is_strong_password(password):
        return False, 'Password must be: of length 10, have uppercase and lowercase letters, digits and symbols'
    
    # Check if passwords match
    if password != confirm_password:
        return False, 'Passwords do not match'
    
    return True, None

# Email format validation
def is_valid_email(email: str) -> bool:
    """
    Validates email format using regex.
    
    Parameters
    ----------
    email : str
        Email address to validate
    
    Returns
    -------
    bool
        True if email is valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Password strength validation
def is_strong_password(password: str) -> bool:
    """
    Checks if password meets strength requirements.
    
    Parameters
    ----------
    password : str
        Password to validate
    
    Returns
    -------
    bool
        True if password is strong, False otherwise
    """
    special_symbols = "!@#$%^&*()"

    return (len(password) >= 10 and 
            any(c.isupper() for c in password) and
            any(c.islower() for c in password) and
            any(c.isdigit() for c in password) and
            any(c in special_symbols for c in password)
            )

def validate_file_upload(data) -> Tuple[list, list]:
    """
    Validates uploaded file.

    Parameters
    ----------
    data : dict or MultiDict
        The uploaded form data

    Returns
    -------
    Tuple[list, list]
        A tuple containing (errors, status_codes)
        errors: list of error messages
        status_codes: list of corresponding HTTP status codes
    """
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    errors = []
    status_codes = []

    if data is None:
        errors.append("[validate_file_upload] No form data provided")
        status_codes.append(500)  # Internal Server Error
        return errors, status_codes

    file = data.getlist('files')[0] if 'files' in data and data.getlist('files') else None

    if not file or file.filename == '':
        errors.append('[validate_file_upload] No selected file')
        status_codes.append(400)  # Bad Request
        return errors, status_codes

    if not allowed_file(file.filename):
        errors.append(f"[validate_file_upload] File {file.filename} is not a PDF")
        status_codes.append(400)  # Bad Request
        return errors, status_codes

    # Check file size more efficiently
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning

    if file_size > MAX_FILE_SIZE:
        errors.append(f"[validate_file_upload] File {file.filename} is too large (max 10MB)")
        status_codes.append(400)  # Bad Request
        return errors, status_codes

    return errors, status_codes


# Chat request validation
def validate_chat_request(data: dict) -> Tuple[list, list, str, str, str, str]:
    """Validate chat request data"""

    MAX_HINTS_LENGTH = 500
    MAX_QUESTION_LENGTH = 1000

    errors = []
    status_codes = []

    # Check required fields
    if not data:
        errors.append("[validate_chat_request] No form data provided")

    if not data.get('hints'):
        errors.append("[validate_chat_request] Hints are required")
        status_codes.append(400)  # Bad Request
    if not data.get('question'):
        errors.append("[validate_chat_request] Question is required")
        status_codes.append(400)  # Bad Request
    
    file_id = data.get('file_id', '').strip()
    conversation_id = data.get('conversation_id', '').strip()
    
    if not file_id and not conversation_id:
        errors.append("[validate_chat_request] Internal Server Error. Please try again.")
        status_codes.append(500)  # Internal Server Error

    # convert IDs to integers if possible
    try:
        file_id = int(file_id) if file_id is not None else None
        conversation_id = int(conversation_id) if conversation_id is not None else None
    except ValueError:
        errors.append("[validate_chat_request] Invalid type for file_id or conversation_id")
        status_codes.append(400)  # Bad Request

    # Validate hints length
    hints = data.get('hints', '')
    if len(hints) > MAX_HINTS_LENGTH:
        errors.append(f"[validate_chat_request] Hints must be less than {MAX_HINTS_LENGTH} characters")
        status_codes.append(400)  # Bad Request
    
    # Validate question length
    question = data.get('question', '')
    if len(question) > MAX_QUESTION_LENGTH:
        errors.append(f"[validate_chat_request] Question must be less than {MAX_QUESTION_LENGTH} characters")
        status_codes.append(400)  # Bad Request

    print(f"[validate_chat_request]: File id: {file_id}, {conversation_id}, {hints}, {question}")
    return errors, status_codes, int(file_id) , conversation_id, question, hints
