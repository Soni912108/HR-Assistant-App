# builtin modules
from datetime import datetime
# third-party modules
from flask import (
    Blueprint,
    jsonify,
    request,
    render_template
    )
from flask_login import login_required, current_user

from openai import APIError, RateLimitError
from werkzeug.utils import secure_filename
# local modules
from backend.utils.assistant import assistant
from backend.utils.file_utils import extract_text_secure 
from backend.database.models import Conversations, Files
from backend import db
from backend.utils.helpers import validate_chat_request, validate_file_upload

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

    data = request.files
    files = data.getlist('files')
    if not files or len(files) == 0:
        return jsonify({"status": "error", "message": "No file part in the request"}), 400
    # check the len of files, if more than 1, return error
    if len(data.getlist('files')) != 1:
        return jsonify({"status": "error", "message": "Only single file upload is supported at this time."}), 400
    
    conversation_id = request.form.get('conversation_id')
    if not conversation_id or not conversation_id.isdigit():
        return jsonify({"status": "error", "message": "Missing conversation id"}), 500
    # Get the current conversation
    conversation = Conversations.query.filter_by(id=int(conversation_id), user=current_user.id).first_or_404()

    errors, status_codes = validate_file_upload(data)
    for error, status_code in zip(errors, status_codes):
        return jsonify({"status": "error", "message": error}), status_code

    try:
        # Process the first file (single file upload for now)
        file = files[0]
        
        # Extract text from PDF
        text_content = extract_text_secure(file)
        print(f"Using existing conversation with ID: {conversation.id} for the uploaded file by user ID: {current_user.id}")
        # update the existing conversation data
        conversation.user_message = 'File uploaded'
        conversation.bot_message = 'File received. You can now ask questions about its content.'
        conversation.time_of_message = datetime.now()
        db.session.commit()
        
        # Create file record linked to the conversation
        file_record = Files(
            conversation_id=int(conversation_id),
            file_name=secure_filename(file.filename),
            text_version_of_the_file=text_content
        )
        db.session.add(file_record)
        db.session.commit()
        
        print(f"Created file record with ID: {file_record.id} linked to conversation ID: {conversation.id}")
        return jsonify({
            "status": "success",
            "message": "File uploaded successfully",
            "file_id": file_record.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error processing file: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error processing file: {str(e)}"
        }), 500


@chat_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """
    Handle chat messages using file_id from previously uploaded files.
    Accepts JSON and form-data (multipart/form-data / application/x-www-form-urlencoded).
    Only returns question and answer in a live chat style.
    """
    print(f"Request received: {request.content_type}")
    if request.method != 'POST':
        return jsonify({"status": "error", "message": "Method not allowed"}), 405

    # Support JSON and form-data
    if request.is_json:
        data = request.get_json(silent=True)
    else:
        # covers multipart/form-data and application/x-www-form-urlencoded
        data = request.form.to_dict() if request.form else None

    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    errors, status_codes, file_id, conversation_id, question, hints = validate_chat_request(data)

    for error, status_code in zip(errors, status_codes):
        return jsonify({"status": "error", "message": error}), status_code

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
        assistant_response = assistant(hints, question, file_content)

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
            return jsonify({
                "status": "error",
                "message": "Error saving conversation"
            }), 500
        # Return the answer
        return jsonify({
            "status": "success",
            "assistant_response": assistant_response,
            "conversation_id": conversation.id
        }), 200
    
    except RateLimitError as e:
        return jsonify({
            "status": "error", "message": "Rate limit exceeded. Please try again later."
        }), 429
    except APIError as e:
        return jsonify({
            "status": "error", "message": "Assistant service temporarily unavailable"
        }), 503
    except Exception as e:
        return jsonify({
            "status": "error", "message": "Error generating response"
        }), 500
