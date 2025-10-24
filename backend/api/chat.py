# builtin modules
from datetime import datetime
import os
import uuid
# third-party modules
from flask import (
    Blueprint,
    jsonify,
    session,
    request,
    render_template,
    current_app
    )
from flask_login import login_required, current_user
from openai import RateLimitError, APIError
from werkzeug.utils import secure_filename
# local modules
from backend.utils.assistant import assistant
from backend.utils.file_reader import extract_text_from_pdf_pypdf2 
from backend.database.models import Conversations, Contact_Forms, Files
from backend import db
from backend.utils.helpers import validate_chat_request

chat_bp = Blueprint('chat', __name__)



@chat_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """
    This function renders the dashboard page for the user.
    Parameters:
        None
    Returns:
        A rendered dashboard.html template.
    """
    return render_template('dashboard.html')

# LEFT HERE, MAKE SURE THAT THE FILE UPLOADED IS ONE(NOT MULTIPLE) AND SEPARATE THE CODE BETTER INSIDE THE CHAT()
# 

@chat_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """
    Handle chat messages between user and assistant with proper validation and error handling.
    
    Expected form data:
    - hints: String containing instructions for the assistant
    - question: User's question
    - files: List of PDF files
    
    Returns JSON response with assistant's answer or error message.
    """
    try:
        # Validate request method and content type
        if request.method != 'POST':
            return jsonify({
                "status": "error", 
                "message": "Method not allowed"
            }), 405
            
        if not request.form:
            return jsonify({
                "status": "error", 
                "message": "No form data provided"
            }), 400
        
        # Extract and validate form data
        form_data = request.form
        files = request.files.getlist('files')
        
        # Additional validation for form data structure
        if not form_data:
            return jsonify({
                "status": "error", 
                "message": "No form data provided"
            }), 400
        
        # Check if files are properly uploaded
        if not files or all(file.filename == '' for file in files):
            return jsonify({
                "status": "error",
                "message": "No valid files uploaded"
            }), 400
        
        # Validate request data
        validation_errors = validate_chat_request(form_data, files)
        if validation_errors:
            return jsonify({
                "status": "error",
                "message": "Validation failed",
                "errors": validation_errors
            }), 400
        
        # Extract validated data
        hints = form_data.get('hints', '').strip()
        question = form_data.get('question', '').strip()
        
        # Process files and extract text
        file_contents = []
        file_records = []
        
        for file in files:
            try:
                # Extract text from PDF
                text_content = extract_text_from_pdf_pypdf2(file)
                file_contents.append(text_content)
                
                # Create file record for database
                file_record = Files(
                    user=current_user.id,
                    file_name=secure_filename(file.filename),
                    text_version_of_the_file=text_content
                )
                file_records.append(file_record)
                
            except Exception as e:
                current_app.logger.error(f"Error processing file {file.filename}: {str(e)}")
                return jsonify({
                    "status": "error",
                    "message": f"Error processing file {file.filename}"
                }), 400
        
        # Combine all file contents
        combined_file_content = "\n\n".join(file_contents)
        
        # Call assistant function
        try:
            assistant_response = assistant(hints, question, combined_file_content)
        except RateLimitError as e:
            return jsonify({
                "status": "error",
                "message": "Rate limit exceeded. Please try again later."
            }), 429
        except APIError as e:
            current_app.logger.error(f"OpenAI API error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Assistant service temporarily unavailable"
            }), 503
        except Exception as e:
            current_app.logger.error(f"Assistant error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Error generating response"
            }), 500
        
        # Save to database with proper transaction handling
        try:
            # Add file records first
            for file_record in file_records:
                db.session.add(file_record)
            db.session.flush()  # Get file IDs
            
            # Create conversation record with first file ID
            conversation = Conversations(
                user=current_user.id,
                file_id=file_records[0].id if file_records else None,
                user_message=question,
                bot_message=assistant_response,
                time_of_message=datetime.now(),
                hints=hints
            )
            db.session.add(conversation)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Error saving conversation"
            }), 500
        
        # Return successful response
        return jsonify({
            "status": "success",
            "assistant_response": assistant_response,
            "conversation_id": conversation.id
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Unexpected error in messages endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500
    

@chat_bp.route('/new_contact_form', methods=['POST'])
@login_required
def new_form():
    """
    Handle new contact form submissions with proper validation.
    """
    try:
        if request.method != 'POST':
            return jsonify({
                "status": "error", 
                "message": "Method not allowed"
            }), 405
            
        if not request.json:
            return jsonify({
                "status": "error", 
                "message": "No JSON data provided"
            }), 400
        
        data = request.json
        user_email = data.get('email', '').strip()
        user_message = data.get('message', '').strip()
        
        # Validate input
        if not user_email or not user_message:
            return jsonify({
                "status": "error",
                "message": "Email and message are required"
            }), 400
        
        if len(user_message) > 500:
            return jsonify({
                "status": "error",
                "message": "Message must be less than 500 characters"
            }), 400
        
        # Create contact form record
        try:
            new_form = Contact_Forms(
                user=current_user.id, 
                user_email=user_email, 
                user_message=user_message
            )
            db.session.add(new_form)
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Contact form submitted successfully"
            }), 200
            
        except Exception as e:
            db.session.rollback()
            print(f"Database error in contact form: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Error saving contact form"
            }), 500
            
    except Exception as e:
        print(f"Unexpected error in contact form: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500
