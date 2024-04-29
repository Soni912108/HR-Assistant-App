from backend.views import app
from backend.models import db

app = app

with app.app_context():
    db.create_all()
