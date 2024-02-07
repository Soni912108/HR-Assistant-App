from backend.assistant import assistant
from backend.file_reader import extract_text_from_pdf_pypdf2 
from backend.models import app,db,User,Conversations,Contact_Forms
from flask import render_template, request, redirect, session, url_for, flash,jsonify,after_this_request
from werkzeug.security import generate_password_hash,check_password_hash
from openai.error import RateLimitError
from datetime import datetime


@app.route('/')
def home():
    return render_template('index.html')


def handle_errors_and_redirect(error_message, category='danger', redirect_url=None):
    """
    A function to handle errors and redirect the user.

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
    Union[Response, TemplateResponse]
        A Response or TemplateResponse object, depending on whether a redirect URL was provided.
    """

    flash(error_message, category)
    return redirect(redirect_url) if redirect_url else render_template(request.endpoint + '.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    This function handles the login process for the user.

    Parameters:
        username (str): The username of the user.
        email (str): The email of the user.
        password (str): The password of the user.

    Returns:
        redirect: If the login is successful, it redirects the user to the dashboard page.
        error message: If the login is unsuccessful, it displays an error message.

    """
    if request.method == 'GET':
        return render_template('login.html')
    
    elif request.method == 'POST':
        # Get user input from the login form
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if the username is in the database
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_user:
            if existing_email:
                # Check if the password is correct
                if check_password_hash(existing_user.password, password):
                    # Login the user
                    session['username'] = username
                    return redirect(url_for('dashboard'))
                else:
                    return handle_errors_and_redirect('Incorrect data.')
            else:
                return handle_errors_and_redirect('Incorrect data.')
        else:
            return handle_errors_and_redirect('No username found.Try to register.')


@app.route('/logout', methods=['POST'])
def logout():
    """
    This function handles the logout process for the user.

    No parameters are required for this function.

    Returns:
        redirect: If the logout is successful, it redirects the user to the home page.
    """
    session.pop('username', None)
    session.pop('password', None)
    session.pop('email', None)
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    This function handles the registration process. It supports both GET and POST methods.
    If the method is GET, it simply renders the registration page.
    If the method is POST, it processes the form data and registers the user.
    """
    # If the request method is GET, render the registration page
    if request.method == 'GET':
        return render_template('register.html')

    # If the request method is POST, process the registration form
    elif request.method == 'POST':
        # Get user input from the registration form
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        # Check if the username is already in use
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            # If the username is taken, redirect the user back to the registration page with an error message
            return handle_errors_and_redirect('Username is already in use. Please choose a different one.', 'danger', url_for('register'))

        # Check if the email is already in use
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            # If the email is taken, redirect the user back to the registration page with an error message
            return handle_errors_and_redirect('Email is already registered. Please use a different email.', 'danger', url_for('register'))

        # Check if the password meets the criteria (e.g., length, complexity)
        if len(password) < 8:
            # If the password is too short, redirect the user back to the registration page with an error message
            return handle_errors_and_redirect('Password must be at least 8 characters long.', 'danger', url_for('register'))
        if password != confirm_password:
            # If the passwords do not match, redirect the user back to the registration page with an error message
            return handle_errors_and_redirect('Passwords do not match.', 'danger', url_for('register'))
        
        # Hash the password before storing it in the database
        hashed_password = generate_password_hash(password, method='pbkdf2:sha1', salt_length=8)

        # Create a new user
        new_user = User(username=username, email=email, password=hashed_password)

        # Add the user to the database
        db.session.add(new_user)
        db.session.commit()

        # Log in the user and redirect them to the dashboard page
        session['username'] = username
        flash('Registration successful! You can now log in.', 'success')

        return redirect(url_for('dashboard'))

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """
    This function renders the dashboard page for the user.
    Parameters:
        None
    Returns:
        A rendered dashboard template.
    """
    username = session.get('username')
    if username:
        @after_this_request
        def add_header(response):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response

        return render_template('dashboard.html')
    else:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('login'))



@app.route('/chat', methods=['POST'])
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
            # Extract data from form
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
    

@app.route('/new_contact_form', methods=['POST'])
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
    