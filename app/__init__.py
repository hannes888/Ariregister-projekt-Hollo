from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from tenacity import retry, wait_fixed, stop_after_attempt
import os

db = SQLAlchemy()


@retry(wait=wait_fixed(2), stop=stop_after_attempt(5))
def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    app.config['DEBUG'] = True
    db.init_app(app)

    with app.app_context():
        from .controllers import company_controller
        app.register_blueprint(company_controller.bp)
        db.create_all()

        os.system('python populate_db_script.py')

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0')
