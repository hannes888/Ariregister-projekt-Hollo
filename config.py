
class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:docker@flask_db:5432/rik'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///testing.db'
