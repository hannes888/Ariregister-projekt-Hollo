import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Individual, LegalEntity

# Database connection
DATABASE_URL = "postgresql://postgres:docker@flask_db:5432/rik"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()


# Sample data
individuals_data = [
    {"first_name": "John", "last_name": "Doe", "personal_code": "12345678901"},
    {"first_name": "Jane", "last_name": "Smith", "personal_code": "23456789012"},
    {"first_name": "Alice", "last_name": "Johnson", "personal_code": "34567890123"},
    {"first_name": "Bob", "last_name": "Brown", "personal_code": "45678901234"},
]

legal_entities_data = [
    {"name": "Example Corp", "registration_code": "1234567"},
    {"name": "Sample LLC", "registration_code": "2345678"},
    {"name": "Test Inc", "registration_code": "3456789"},
    {"name": "Demo Ltd", "registration_code": "4567890"},
]

# Populate individuals table
for data in individuals_data:
    individual = Individual(
        first_name=data["first_name"],
        last_name=data["last_name"],
        personal_code=data["personal_code"]
    )
    if session.query(Individual).filter_by(personal_code=data["personal_code"]).first() is None:
        session.add(individual)

# Populate legal_entities table
for data in legal_entities_data:
    legal_entity = LegalEntity(
        name=data["name"],
        registration_code=data["registration_code"]
    )
    if session.query(LegalEntity).filter_by(registration_code=data["registration_code"]).first() is None:
        session.add(legal_entity)

# Commit the session to save the data
session.commit()

# Close the session
session.close()

print("Data has been populated successfully.")