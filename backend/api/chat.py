# builtin modules
from datetime import datetime
# third-party modules
from flask import (
    Blueprint,
    jsonify,
    session,
    request
    )
from openai import RateLimitError
# local modules
from backend.utils.assistant import assistant
from backend.utils.file_reader import extract_text_from_pdf_pypdf2 
from backend.database.models import db,Conversations,Contact_Forms


chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['POST'])
def messages():
    """
    This function handles the chat messages between the user and the assistant.

    POST requests with form data are expected, where the form data should contain the following keys:

    - hints: A JSON string containing the code hints.
    - question: The user's question.
    - files: A list of file objects uploaded by the user.

    The function should extract the hints, question, and files from the form data, and then call the assistant function 
    with these inputs. The assistant function should return a response, which should be returned to the user as a JSON response.

    If the request is not a POST request or does not contain form data, the function should return an error response.

    This function should also create a new conversation record in the database, with the user's message, the assistant's response, 
    and the hints.
    """
    try:
        # Check if the request has form data
        if request.method == 'POST' and request.form:
            # Extract data from the form
            hints = request.form['hints']
            question = request.form['question']
            # Access files using request.files
            files = request.files.getlist('files')
            if len(files) > 0 and len(hints) > 0 and len(question):
                # Handle files as needed (e.g., extract text from PDFs)
                file_contents = "\n\n".join(extract_text_from_pdf_pypdf2(file) for file in files)
                # Call assistant function with hints, question, and file text
                assistant_response = assistant(hints, question, file_contents)
                # Create a new conversation in the database
                current_date = datetime.now()
                new_conversation = Conversations(user=session['username'], user_message=question, bot_message=assistant_response,time_of_message=current_date, hints=hints)
                db.session.add(new_conversation)
                db.session.commit()
                # Return a response to the client
                return jsonify({"status": "success", "assistant_response": assistant_response})
            else:
                return jsonify({"status": "error", "message": "No Data Provided.Please provide hints, question, and files to continue."})
        else:
            return jsonify({"status": "error", "message": "Bad request"})
    except RateLimitError as e:
        # Handle rate limit error
        return jsonify({"status": "error", "message": str(e)})
    

@chat_bp.route('/new_contact_form', methods=['POST'])
def new_form():
    """
    This function handles the new contact form.
    """
    if request.method == 'POST': 
        # Parse JSON data from the request
        data = request.json
        # Get user input from the new contact form
        user_email = data.get('email')
        user_message = data.get('message')
        # Create a new record in the database 
        new_form = Contact_Forms(user=session.get('username'), user_email=user_email, user_message=user_message)
        db.session.add(new_form)
        db.session.commit()
        # Return a response to the client
        return jsonify({"status": "Success"})
    
