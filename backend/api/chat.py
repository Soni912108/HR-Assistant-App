# builtin modules
from datetime import datetime
# third-party modules
from flask import (
    Blueprint,
    jsonify,
    request,
    render_template,
    current_app
    )
from flask_login import login_required, current_user
from openai import RateLimitError, APIError
from werkzeug.utils import secure_filename
# local modules
from backend.utils.assistant import assistant
from backend.utils.file_utils import extract_text_from_pdf_pypdf2 
from backend.database.models import Conversations, Contact_Forms, Files
from backend import db
from backend.utils.helpers import validate_chat_request

chat_bp = Blueprint('chat', __name__)



@chat_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """
    This function renders the dashboard page for the user.
    A default conversation ID is created, but it will be replaced 
    when a file is uploaded (new conversation is created for each file upload).
    Parameters:
        None
    Returns:
        A rendered dashboard.html template.
    """
    # Create a default conversation id for the user (will be replaced when file is uploaded)
    conversation = Conversations(
        user=current_user.id,
        user_message='Welcome',
        bot_message='Please upload a PDF file to get started.',
        time_of_message=datetime.now(),
        hints='Default conversation start.'
    )
    db.session.add(conversation)
    db.session.commit()
    # Log the conversation creation message
    print(f"Created default conversation with ID: {conversation.id} for user ID: {current_user.id}")
    # Render the dashboard template, passing the conversation ID
    return render_template('dashboard.html', conversation_id=conversation.id)


@chat_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """
    Handle file uploads separately from chat.
    Creates a new file record and links it to a new conversation.
    Returns file_id and conversation_id for use in chat requests.
    """
    if request.method != 'POST':
        return jsonify({"status": "error", "message": "Method not allowed"}), 405

    files = request.files.getlist('files')
    
    if not files or all(f.filename == '' for f in files):
        return jsonify({"status": "error", "message": "At least one PDF file is required."}), 400

    try:
        # Process the first file (assuming single file upload for now)
        file = files[0]
        
        # Extract text from PDF
        text_content = extract_text_from_pdf_pypdf2(file)
        
        # Create a new conversation for this file upload
        conversation = Conversations(
            user=current_user.id,
            user_message='File uploaded',
            bot_message='File uploaded successfully. You can now ask questions about this file.',
            time_of_message=datetime.now(),
            hints='File upload conversation'
        )
        db.session.add(conversation)
        db.session.flush()  # Get conversation ID
        
        # Create file record linked to the conversation
        file_record = Files(
            conversation_id=conversation.id,
            file_name=secure_filename(file.filename),
            text_version_of_the_file=text_content
        )
        db.session.add(file_record)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "File uploaded successfully",
            "file_id": file_record.id,
            "conversation_id": conversation.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error processing file: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error processing file: {str(e)}"
        }), 400


@chat_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """
    Handle chat messages using file_id from previously uploaded files.
    Only returns question and answer in a live chat style.
    """
    if request.method != 'POST':
        return jsonify({"status": "error", "message": "Method not allowed"}), 405

    if not request.form and not request.json:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    # Support both form data and JSON
    data = request.form if request.form else request.json
    
    hints = data.get('hints', '').strip()
    question = data.get('question', '').strip()
    file_id = data.get('file_id', '').strip()
    conversation_id = data.get('conversation_id', '').strip()

    if not question or not hints:
        return jsonify({"status": "error", "message": "Question and hints are required."}), 400

    if not file_id:
        return jsonify({"status": "error", "message": "File ID is required. Please upload a file first."}), 400

    if not conversation_id:
        return jsonify({"status": "error", "message": "Conversation ID is required."}), 400

    try:
        # Retrieve file from database using file_id
        file_record = Files.query.filter_by(id=file_id, conversation_id=conversation_id).first()
        
        if not file_record:
            return jsonify({
                "status": "error",
                "message": "File not found or does not belong to this conversation."
            }), 404

        # Get file content
        file_content = file_record.text_version_of_the_file

        # Call assistant function
        try:
            assistant_response = assistant(hints, question, file_content)
        except RateLimitError as e:
            return jsonify({
                "status": "error",
                "message": "Rate limit exceeded. Please try again later."
            }), 429
        except APIError as e:
            print(f"OpenAI API error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Assistant service temporarily unavailable"
            }), 503
        except Exception as e:
            print(f"Assistant error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Error generating response"
            }), 500

        # Save conversation to database
        try:
            conversation = Conversations(
                user=current_user.id,
                user_message=question,
                bot_message=assistant_response,
                time_of_message=datetime.now(),
                hints=hints
            )
            db.session.add(conversation)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Database error: {str(e)}")
            # Still return response even if saving fails

        # Return only question and answer (live chat style)
        return jsonify({
            "status": "success",
            "assistant_response": assistant_response,
            "conversation_id": conversation.id
        }), 200

    except Exception as e:
        print(f"Unexpected error in chat endpoint: {str(e)}")
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
