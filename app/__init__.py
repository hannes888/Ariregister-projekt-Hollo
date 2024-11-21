from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    app.config['DEBUG'] = True
    db.init_app(app)

    with app.app_context():
        from .controllers import company_controller
        app.register_blueprint(company_controller.bp)
        db.create_all()

    return app
