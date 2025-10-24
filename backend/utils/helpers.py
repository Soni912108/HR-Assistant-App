# builtin modules
import re
import os
import uuid
from typing import Optional, Union, Tuple

# third-party modules
from flask import Response, render_template, flash, redirect, request
from werkzeug.utils import secure_filename

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


def validate_registration_data(email: str, username: str, password: str, confirm_password: str) -> Tuple[bool, Optional[str]]:
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
    if len(username) < 3:
        return False, 'Username must be at least 3 characters long'
    
    if len(username) > 20:
        return False, 'Username must be less than 20 characters long'
    
    # Validate password length
    if len(password) < 10:
        return False, 'Password must be at least 10 characters long'
    
    # Check if passwords match
    if password != confirm_password:
        return False, 'Passwords do not match'
    
    return True, None


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
    return (len(password) >= 8 and 
            any(c.isupper() for c in password) and
            any(c.islower() for c in password) and
            any(c.isdigit() for c in password))


# Configuration constants
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILES = 5
MAX_HINTS_LENGTH = 500
MAX_QUESTION_LENGTH = 1000

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_chat_request(form_data, files):
    """Validate chat request data"""
    errors = []
    
    # Check required fields
    if not form_data.get('hints'):
        errors.append("Hints are required")
    if not form_data.get('question'):
        errors.append("Question is required")
    if not files:
        errors.append("At least one file is required")
    
    # Validate hints length
    hints = form_data.get('hints', '')
    if len(hints) > MAX_HINTS_LENGTH:
        errors.append(f"Hints must be less than {MAX_HINTS_LENGTH} characters")
    
    # Validate question length
    question = form_data.get('question', '')
    if len(question) > MAX_QUESTION_LENGTH:
        errors.append(f"Question must be less than {MAX_QUESTION_LENGTH} characters")
    
    # Validate files
    if len(files) > MAX_FILES:
        errors.append(f"Maximum {MAX_FILES} files allowed")
    
    for file in files:
        if file.filename == '':
            errors.append("Empty filename not allowed")
        elif not allowed_file(file.filename):
            errors.append(f"File {file.filename} is not a PDF")
        else:
            # Check file size more efficiently
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size > MAX_FILE_SIZE:
                errors.append(f"File {file.filename} is too large (max 10MB)")
    
    return errors
