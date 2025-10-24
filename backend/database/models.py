
from flask_mail import Message
from sqlalchemy.event import listens_for

from backend import db, mail

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Conversations(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    user_message = db.Column(db.String(140), nullable=False)
    bot_message = db.Column(db.String(140), nullable=False)
    time_of_message = db.Column(db.DateTime, nullable=False)
    hints = db.Column(db.String(500), nullable=False)
    def __repr__(self):
        return f"Conversations('{self.user}', '{self.user_message}', '{self.bot_message}', '{self.time_of_message}','{self.hints}')"
    

class Files(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    text_version_of_the_file = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"Files('{self.user}', '{self.text_version_of_the_file}')"
    

class Contact_Forms(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    user_email = db.Column(db.String(120), nullable=False)
    user_message = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return f"Client('{self.user}', submitted a new form '{self.user_message[:50]}')"
    

@listens_for(Contact_Forms, "after_insert")
def send_email_after_insert(mapper, connection, target):
    admin_emails = mail.config['ADMINS']
    for admin_email in admin_emails:
        msg = Message("New Contact Form Submission",
                      recipients=[admin_email])
        msg.body = f"New contact form submission from {target.user} ({target.user_email}): \n\n{target.user_message}"
        mail.send(msg)
