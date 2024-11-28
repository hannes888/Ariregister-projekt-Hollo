import unittest
from datetime import date

from app.services.app_service import AppService
from app.models import Company, Shareholder, Individual, LegalEntity
from app.extensions import db
from flask import Flask


class TestUpdateShareAmountService(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
            self.company = Company(
                name='Test Company',
                registration_code='123456',
                establishment_date=date(2020, 1, 1),
                total_capital=100000
            )
            db.session.add(self.company)
            db.session.commit()
            self.company = Company.query.filter_by(registration_code='123456').first()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_update_share_amount(self):
        with self.app.app_context():
            individual = Individual(first_name='John', last_name='Doe', personal_code='1234567890')
            legal_entity = LegalEntity(name='Test Entity', registration_code='9876543210')
            db.session.add(individual)
            db.session.add(legal_entity)
            db.session.commit()

            shareholder1 = Shareholder(company_id=self.company.id, individual_id=individual.id, share_amount=1000)
            shareholder2 = Shareholder(company_id=self.company.id, legal_entity_id=legal_entity.id, share_amount=2000)
            db.session.add(shareholder1)
            db.session.add(shareholder2)
            db.session.commit()

            new_share_amounts = [
                {'individual_id': individual.id, 'share_amount': 1500},
                {'legal_entity_id': legal_entity.id, 'share_amount': 2500}
            ]

            AppService.update_share_amount(self.company.registration_code, new_share_amounts)

            updated_shareholder1 = Shareholder.query.filter_by(individual_id=individual.id).first()
            updated_shareholder2 = Shareholder.query.filter_by(legal_entity_id=legal_entity.id).first()

            self.assertEqual(updated_shareholder1.share_amount, 1500)
            self.assertEqual(updated_shareholder2.share_amount, 2500)


if __name__ == '__main__':
    unittest.main()