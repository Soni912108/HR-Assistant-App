from flask_login import UserMixin

from backend import db

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
    
    user_message = db.Column(db.String(140), nullable=False)
    bot_message = db.Column(db.String(140), nullable=False)
    time_of_message = db.Column(db.DateTime, nullable=False)
    hints = db.Column(db.String(500), nullable=False)

    files = db.relationship('Files', backref='conversation', lazy=True)

    def __repr__(self):
        return f"Conversations('User ID: {self.user.id}', 'Time of Message: {self.time_of_message}', 'Hints: {self.hints}')"
    

class Files(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False, index=True)

    file_name = db.Column(db.String(120), nullable=False)
    text_version_of_the_file = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"Files('File Name: {self.file_name} in Conversation ID: {self.conversation_id}')"
    
