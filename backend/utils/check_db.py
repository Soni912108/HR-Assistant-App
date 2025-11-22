import backend.configs.config as project_paths

from backend import create_app,db # db here is -> db = SQLAlchemy()
from backend.database.models import User, Conversations, Files

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

        if users_empty and conversations_empty and files_empty:
            return False  # Database is not seeded
        return True  # Database has some data

if __name__ == "__main__":
    from dotenv import load_dotenv
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