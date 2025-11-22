
# third-party modules
from flask import (
    Blueprint,
    render_template, request, redirect, 
    session, url_for, flash,
    after_this_request
    )
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash,check_password_hash

# local modules
from backend.database.models import User
from backend import db
from backend.utils.helpers import validate_registration_data

routes_bp = Blueprint('routes', __name__)

@routes_bp.route('/')
def home():
    return render_template('index.html')

# Authentication
@routes_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    # Support JSON and form-data
    if request.is_json:
        data = request.get_json(silent=True)
    else:
        # covers multipart/form-data and application/x-www-form-urlencoded
        data = request.form.to_dict() if request.form else None

    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    remember = data.get("remember", False)
 
    # Input validation
    if not email or not password:
        flash('Please fill in all fields', 'error')
        return redirect(url_for("routes.login"))

    # Find user by email
    user = User.query.filter_by(email=email).first()
    # Check if user exists and password is correct
    if user and check_password_hash(user.password, password):
        login_user(user, remember=remember)
        flash('Login successful!', 'success')
        return redirect(url_for("chat.dashboard"))
    else:
        flash('Invalid email or password', 'error')
        return redirect(url_for("routes.login"))


@routes_bp.route("/register", methods=["GET", "POST"])
def register():
    # Debug prints removed
    if request.method == "GET":
        return render_template("register.html")

    # Support JSON and form-data
    if request.is_json:
        data = request.get_json(silent=True)
    else:
        # covers multipart/form-data and application/x-www-form-urlencoded
        data = request.form.to_dict() if request.form else None

    # POST request handling
    email = data.get("email", "").strip().lower()
    username = data.get("username", "").strip().lower()
    password = data.get("password", "").strip()
    confirm_password = data.get("confirm-password", "").strip()

    # Input validation using helper function
    is_valid, error_message = validate_registration_data(email, username, password, confirm_password)
    if not is_valid:
        flash(error_message, 'error')
        return redirect(url_for("routes.register"))

    # Check if user already exists
    existing_user = User.query.filter(
        (User.email == email) | (User.username == username)
    ).first()

    if existing_user:
        if existing_user.email == email:
            flash('Email address already exists', 'error')
        else:
            flash('Username already exists', 'error')
        return redirect(url_for("routes.register"))

    try:
        # Create new user
        new_user = User(
            email=email,
            username=username,
            password=generate_password_hash(password, method="pbkdf2:sha256")
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for("routes.login"))
    
    except Exception as e:
        db.session.rollback()
        flash('An error occurred during registration. Please try again.', 'error')
        return redirect(url_for("routes.register"))


@routes_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("routes.login"))