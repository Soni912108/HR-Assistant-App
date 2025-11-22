import backend.configs.config as project_paths

import random
import string

from backend import create_app,db # db here is -> db = SQLAlchemy()
from backend.database.models import User, Conversations

from faker import Faker
# Initialize Faker for generating random data
fake = Faker()

def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def create_test_users(n):
    """Create test users (both persons and companies)"""
    users = []
    
    # Create persons
    for _ in range(n):
        person = User(
            email=f"person_{generate_random_string()}@example.com",
            username=fake.first_name(),
            password="test123", # this should be hashed...
        )
        users.append(person)
    
    return users

def create_test_conversations(user_id, n):
    """Create test conversations for a given user"""
    conversations = []
    for _ in range(n):
        conversation = Conversations(
            user=user_id,
            user_message=fake.sentence(),
            bot_message=fake.sentence(),
            time_of_message=fake.date_time_between(start_date='-30d', end_date='now'),
            hints=fake.text(max_nb_chars=100)
        )
        conversations.append(conversation)
    return conversations

# main function
def seed_database():
    """Main function to seed the database with test data"""
    # Load environment variables
    load_dotenv()
    # create app
    app = create_app()

    with app.app_context():
        try:
            # Create and commit users first to get their IDs
            print("Creating test users...")
            users = create_test_users(10)
            db.session.add_all(users)
            db.session.flush()  # This assigns IDs without committing
    
            # Create and commit conversations for each user
            print("Creating test conversations...")
            for user in users:
                conversations = create_test_conversations(user.id, n=5)
                db.session.add_all(conversations)
            # Finally commit everything to the database
            db.session.commit()
            print("Database seeded successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding database: {str(e)}")
            raise

if __name__ == "__main__":
    from dotenv import load_dotenv
    seed_database() 