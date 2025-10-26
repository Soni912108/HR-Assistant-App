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
    Parameters:
        None
    Returns:
        A rendered dashboard.html template.
    """
    # create conversation id for the user
    conversation = Conversations(
        user=current_user.id,
        user_message = 'Hello Assistant!',
        bot_message = 'Hello User!',
        time_of_message = datetime.now(),
        hints = 'Default conversation start.'
        )
    db.session.add(conversation)
    db.session.commit()
    # Log the conversation creation message
    print(f"Created default conversation with ID: {conversation.id} for user ID: {current_user.id}")
    # Render the dashboard template, passing the conversation ID
    return render_template('dashboard.html', conversation_id=conversation.id)


# NOTE:
# Maybe add a separate route to load and save the file to sever first,
# and than use the file id in the chat route to link the file to the conversation.
# so that the file remains in client side and user can ask questions later without re-uploading the file.
# if new request to upload a new file, create a new file record and link it to a new conversation.
# this way dont show the conversation but only the question and answer in a live chat style.
# maybe in the future we can add a route to show the conversation history with files linked to each conversation.


@chat_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    if request.method != 'POST':
        return jsonify({"status": "error", "message": "Method not allowed"}), 405

    if not request.form:
        return jsonify({"status": "error", "message": "No form data provided"}), 400

    hints = request.form.get('hints', '').strip()
    question = request.form.get('question', '').strip()
    files = request.files.getlist('files')  # will be a list of FileStorage objects, but only 1 file
    conversation_id = request.form.get('conversation_id', '').strip()

    print("Form Data:", request.form)
    print("Files:", request.files)

    if not question or not hints:
        return jsonify({"status": "error", "message": "Question and hints are required."}), 400

    if not files or all(f.filename == '' for f in files):
        return jsonify({"status": "error", "message": "At least one PDF file is required."}), 400

    file_contents = []

    for file in files:
        try:
            # Example text extraction
            text_content = extract_text_from_pdf_pypdf2(file)
            file_contents.append(text_content)

            Files(
                conversation_id=conversation_id,
                file_name=secure_filename(file.filename),
                text_version_of_the_file=text_content
            )

        except Exception as e:
            current_app.logger.error(f"Error processing file {file.filename}: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Error processing file {file.filename}"
            }), 400

    # ✅ Return success response
    return jsonify({
        "status": "success",
        "assistant_response": f"Processed {len(files)} file(s) successfully."
    }), 200



# @chat_bp.route('/chat', methods=['POST'])
# @login_required
# def chat():
#     """
#     # Handle chat messages between user and assistant with proper validation and error handling.
    
#     # Expected form data:
#     # - hints: String containing instructions for the assistant
#     # - question: User's question
#     # - files: List of PDF files
    
#     # Returns JSON response with assistant's answer or error message.
#     # """
    # # try:
    # # Validate request method and content type
    # if request.method != 'POST':
    #     return jsonify({
    #         "status": "error", 
    #         "message": "Method not allowed"
    #     }), 405
        
    # if not request.form:
    #     return jsonify({
    #         "status": "error", 
    #         "message": "No form data provided"
    #     }), 400
    
    # # Extract and validate form data
    # form_data = request.form
    # print("Form Data:", form_data)
    # # Validate request data
    # validation_errors = validate_chat_request(form_data)
    # if validation_errors:
    #     return jsonify({
    #         "status": "error",
    #         "message": "Validation failed",
    #         "errors": validation_errors
    #     }), 400
    
    # # Extract validated data
    # hints = form_data.get('hints', '').strip()
    # question = form_data.get('question', '').strip()
    # file  = form_data.getlist('files')
    # # Process file and extract text
    # file_contents = []
    # file_records = []
    
    # try:
    #     # Extract text from PDF
    #     text_content = extract_text_from_pdf_pypdf2(file)
    #     file_contents.append(text_content)
        
    #     # Create file record for database
    #     file_record = Files(
    #         user=current_user.id,
    #         file_name=secure_filename(file.filename),
    #         text_version_of_the_file=text_content
    #     )
    #     file_records.append(file_record)
        
    # except Exception as e:
    #     current_app.logger.error(f"Error processing file {file.filename}: {str(e)}")
    #     return jsonify({
    #         "status": "error",
    #         "message": f"Error processing file {file.filename}"
    #     }), 400
        
        # # Combine all file contents
        # combined_file_content = "\n\n".join(file_contents)
        
        # # Call assistant function
        # try:
        #     assistant_response = assistant(hints, question, combined_file_content)
        # except RateLimitError as e:
        #     return jsonify({
        #         "status": "error",
        #         "message": "Rate limit exceeded. Please try again later."
        #     }), 429
        # except APIError as e:
        #     current_app.logger.error(f"OpenAI API error: {str(e)}")
        #     return jsonify({
        #         "status": "error",
        #         "message": "Assistant service temporarily unavailable"
        #     }), 503
        # except Exception as e:
        #     current_app.logger.error(f"Assistant error: {str(e)}")
        #     return jsonify({
        #         "status": "error",
        #         "message": "Error generating response"
        #     }), 500
        
        # # Save to database with proper transaction handling
        # try:
        #     # Add file records first
        #     for file_record in file_records:
        #         db.session.add(file_record)
        #     db.session.flush()  # Get file IDs
            
        #     # Create conversation record with first file ID
        #     conversation = Conversations(
        #         user=current_user.id,
        #         file_id=file_records[0].id if file_records else None,
        #         user_message=question,
        #         bot_message=assistant_response,
        #         time_of_message=datetime.now(),
        #         hints=hints
        #     )
        #     db.session.add(conversation)
        #     db.session.commit()
            
        # except Exception as e:
        #     db.session.rollback()
        #     print(f"Database error: {str(e)}")
        #     return jsonify({
        #         "status": "error",
        #         "message": "Error saving conversation"
        #     }), 500
        
        # # Return successful response
        # return jsonify({
        #     "status": "success",
        #     "assistant_response": assistant_response,
        #     "conversation_id": conversation.id
        # }), 200
        
    # except Exception as e:
    #     print(f"Unexpected error in messages endpoint: {str(e)}")
    #     return jsonify({
    #         "status": "error",
    #         "message": "Internal server error"
    #     }), 500
    

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
