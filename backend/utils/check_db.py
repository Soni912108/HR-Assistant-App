import sys
import os
import random
import string
from datetime import datetime, timedelta

# make project root (parent of 'backend') available on sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
if project_root not in sys.path:
    print(f"Adding {project_root} to sys.path")
    sys.path.insert(0, project_root)
else:
    print(f"{project_root} already in sys.path. Continuing...")

from dotenv import load_dotenv

from backend import create_app,db # db here is -> db = SQLAlchemy()
from backend.database.models import User, Conversations, Files, Contact_Forms

# Query the tables to check if they are empty
def check_table_empty(model):
    """Check if a given table is empty."""
    return db.session.query(model).first() is None

# Check specific rows on a given table
def check_specific_row_exists(model, **kwargs):
    """Check if a specific row exists in a given table based on provided criteria."""
    return db.session.query(model).filter_by(**kwargs).first() is not None

def is_database_seeded():
    """Check if the database has been seeded with initial data."""
    with create_app().app_context():
        users_empty = check_table_empty(User)
        conversations_empty = check_table_empty(Conversations)
        files_empty = check_table_empty(Files)
        contact_forms_empty = check_table_empty(Contact_Forms)

        if users_empty and conversations_empty and files_empty and contact_forms_empty:
            return False  # Database is not seeded
        return True  # Database has some data

if __name__ == "__main__":
    load_dotenv()
    app = create_app()

    with app.app_context():
        if check_specific_row_exists(User, username='testing'):
            print("User 'testing' exists in the database.")
        else:
            print("User 'testing' does not exist in the database.")
        
        if is_database_seeded():
            print("Database is already seeded.")
        else:
            print("Database is not seeded.")