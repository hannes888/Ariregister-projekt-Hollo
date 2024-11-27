from flask import Flask
from tenacity import retry, wait_fixed, stop_after_attempt
import os
from app.controllers import shareholder_controller, company_controller
from app.extensions import db


@retry(wait=wait_fixed(2), stop=stop_after_attempt(5))
def create_app(config_name=None):
    app = Flask(__name__)

    if config_name == 'testing':
        app.config.from_object('config.TestingConfig')
    else:
        app.config.from_object('config.Config')
    app.config['DEBUG'] = True
    db.init_app(app)

    with app.app_context():
        app.register_blueprint(company_controller.company_bp)
        app.register_blueprint(shareholder_controller.shareholder_bp)
        db.create_all()

        os.system('python populate_db_script.py')

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', debug=True)
