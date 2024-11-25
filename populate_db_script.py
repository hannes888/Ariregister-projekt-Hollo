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
    {"first_name": "Charlie", "last_name": "Davis", "personal_code": "56789012345"},
    {"first_name": "Emily", "last_name": "Wilson", "personal_code": "67890123456"},
    {"first_name": "Frank", "last_name": "Miller", "personal_code": "78901234567"},
    {"first_name": "Grace", "last_name": "Taylor", "personal_code": "89012345678"},
    {"first_name": "Henry", "last_name": "Anderson", "personal_code": "90123456789"},
    {"first_name": "Ivy", "last_name": "Thomas", "personal_code": "01234567890"},
    {"first_name": "Jack", "last_name": "Moore", "personal_code": "12345098765"},
    {"first_name": "Kathy", "last_name": "Martin", "personal_code": "23456109876"},
    {"first_name": "Leo", "last_name": "Jackson", "personal_code": "34567210987"},
    {"first_name": "Mia", "last_name": "White", "personal_code": "45678321098"},
    {"first_name": "Nina", "last_name": "Harris", "personal_code": "56789432109"},
    {"first_name": "Oscar", "last_name": "Clark", "personal_code": "67890543210"},
    {"first_name": "Paul", "last_name": "Lewis", "personal_code": "78901654321"},
    {"first_name": "Quinn", "last_name": "Walker", "personal_code": "89012765432"},
    {"first_name": "Rose", "last_name": "Hall", "personal_code": "90123876543"},
    {"first_name": "Sam", "last_name": "Allen", "personal_code": "01234987654"},
    {"first_name": "Tina", "last_name": "Young", "personal_code": "12345098764"},
    {"first_name": "Uma", "last_name": "King", "personal_code": "23456109875"},
    {"first_name": "Victor", "last_name": "Scott", "personal_code": "34567210986"},
    {"first_name": "Wendy", "last_name": "Green", "personal_code": "45678321097"},
    {"first_name": "Xander", "last_name": "Adams", "personal_code": "56789432108"},
]

legal_entities_data = [
    {"name": "Example Corp", "registration_code": "1234567"},
    {"name": "Sample LLC", "registration_code": "2345678"},
    {"name": "Test Inc", "registration_code": "3456789"},
    {"name": "Demo Ltd", "registration_code": "4567890"},
    {"name": "Alpha Co", "registration_code": "5678901"},
    {"name": "Beta Enterprises", "registration_code": "6789012"},
    {"name": "Gamma Solutions", "registration_code": "7890123"},
    {"name": "Delta Services", "registration_code": "8901234"},
    {"name": "Epsilon Group", "registration_code": "9012345"},
    {"name": "Zeta Holdings", "registration_code": "0123456"},
    {"name": "Eta Technologies", "registration_code": "1234568"},
    {"name": "Theta Innovations", "registration_code": "2345679"},
    {"name": "Iota Systems", "registration_code": "3456780"},
    {"name": "Kappa Industries", "registration_code": "4567891"},
    {"name": "Lambda Corp", "registration_code": "5678902"},
    {"name": "Mu Enterprises", "registration_code": "6789013"},
    {"name": "Nu Solutions", "registration_code": "7890124"},
    {"name": "Xi Services", "registration_code": "8901235"},
    {"name": "Omicron Group", "registration_code": "9012346"},
    {"name": "Pi Holdings", "registration_code": "0123457"},
    {"name": "Rho Technologies", "registration_code": "1234569"},
    {"name": "Sigma Innovations", "registration_code": "2345670"},
    {"name": "Tau Systems", "registration_code": "3456781"},
    {"name": "Upsilon Industries", "registration_code": "4567892"},
    {"name": "Upsilon Industries", "registration_code": "5567892"},
    {"name": "Upsilon Industries", "registration_code": "6567892"},
    {"name": "Upsilon Industries", "registration_code": "7567892"},
    {"name": "Upsilon Industries", "registration_code": "8567892"},
    {"name": "Upsilon Industries", "registration_code": "9567892"},
    {"name": "Upsilon Industries", "registration_code": "0567892"},
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