
from flask_mail import Message
from sqlalchemy.event import listens_for
from flask_login import UserMixin

from backend import db, mail

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Conversations(db.Model):

    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False, index=True)
    
    user_message = db.Column(db.String(140), nullable=False)
    bot_message = db.Column(db.String(140), nullable=False)
    time_of_message = db.Column(db.DateTime, nullable=False)
    hints = db.Column(db.String(500), nullable=False)
    def __repr__(self):
        return f"Conversations('User ID: {self.user.id}', 'Time of Message: {self.time_of_message}', 'Hints: {self.hints}')"
    

class Files(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False, index=True)

    file_name = db.Column(db.String(120), nullable=False)
    text_version_of_the_file = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"Files('User ID: {self.user.id}', 'File Name: {self.file_name} in Conversation ID: {self.conversation_id}')"
    

class Contact_Forms(db.Model):
    __tablename__ = 'contact_forms'

    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    user_email = db.Column(db.String(120), nullable=False)
    user_message = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return f"Client('User ID: {self.user.id}', submitted a new form '{self.user_message[:50]}')"
    

@listens_for(Contact_Forms, "after_insert")
def send_email_after_insert(mapper, connection, target):
    admin_emails = mail.config['ADMINS']
    for admin_email in admin_emails:
        msg = Message("New Contact Form Submission",
                      recipients=[admin_email])
        msg.body = f"New contact form submission from {target.user} ({target.user_email}): \n\n{target.user_message}"
        mail.send(msg)
