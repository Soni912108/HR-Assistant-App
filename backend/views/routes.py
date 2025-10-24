
# third-party modules
from flask import (
    Blueprint,
    render_template, request, redirect, 
    session, url_for, flash,
    after_this_request
    )
from werkzeug.security import generate_password_hash,check_password_hash

# local modules
from backend.database.models import User
from backend import db
from backend.utils.helpers import handle_errors_and_redirect


routes_bp = Blueprint('routes', __name__)

@routes_bp.route('/')
def home():
    return render_template('index.html')


@routes_bp.route('/login', methods=['GET', 'POST'])
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
        try:
            existing_user = User.query.filter_by(username=username).first()
            existing_email = User.query.filter_by(email=email).first()

            if existing_user and existing_email:
                # Check if the password is correct
                if check_password_hash(existing_user.password, password):
                    # Login the user
                    session['username'] = username
                    return redirect(url_for('routes.dashboard'))
                else:
                    return handle_errors_and_redirect('Incorrect data.')
            else:
                return handle_errors_and_redirect('Incorrect data.')
        except Exception as e:
            print(f"Database error: {e}")
            return handle_errors_and_redirect('An error occurred. Please try again.')

@routes_bp.route('/logout', methods=['POST'])
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
    return redirect(url_for('routes.home'))


@routes_bp.route('/register', methods=['GET', 'POST'])
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
        flash('Registration successful!', 'success')

        return redirect(url_for('routes.dashboard'))

@routes_bp.route('/dashboard', methods=['GET'])
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

        return render_template('routes.dashboard.html')
    else:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('routes.login'))