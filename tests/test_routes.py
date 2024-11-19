from datetime import datetime

import pytest
from flask import Flask
from app import create_app, db
from app.models import Company, Individual, LegalEntity, Shareholder


@pytest.fixture(scope='function')
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


class TestCreateCompany:

    def test_create_company_success(self, client):
        data = {
            'name': 'TestCompany',
            'registration_code': '12345678',
            'establishment_date': '2020-01-01',
            'total_capital': 5000,
            'shareholders': [
                {
                    'type': 'individual',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'personal_code': '12345678901',
                    'share_amount': 5000
                }
            ]
        }
        response = client.post('/company', json=data)
        print(response.json)
        assert response.status_code == 201
        assert response.json['message'] == 'Company and shareholders created'

    def test_create_company_invalid_name(self, client):
        data = {
            'name': 'Invalid@Name',
            'registration_code': '1234567',
            'establishment_date': '2020-01-01',
            'total_capital': 5000,
            'shareholders': [
                {
                    'type': 'individual',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'personal_code': '12345678901',
                    'share_amount': 5000
                }
            ]
        }

        data['establishment_date'] = datetime.strptime(data['establishment_date'], '%Y-%m-%d').strftime('%Y-%m-%d')

        response = client.post('/company', json=data)
        print(response.json)
        assert response.status_code == 400
        assert response.json['message'] == 'Invalid company name'

    def test_create_company_invalid_registration_code(self, client):
        data = {
            'name': 'Test Company',
            'registration_code': 'invalid_code',
            'establishment_date': '2020-01-01',
            'total_capital': 5000,
            'shareholders': []
        }
        response = client.post('/company', json=data)
        assert response.status_code == 400
        assert response.json['message'] == 'Invalid registration code'

    def test_create_company_invalid_establishment_date(self, client):
        data = {
            'name': 'Test Company',
            'registration_code': '1234567',
            'establishment_date': '2025-01-01',
            'total_capital': 5000,
            'shareholders': []
        }
        response = client.post('/company', json=data)
        assert response.status_code == 400
        assert response.json['message'] == 'Invalid establishment date'

    def test_create_company_invalid_total_capital(self, client):
        data = {
            'name': 'Test Company',
            'registration_code': '1234567',
            'establishment_date': '2020-01-01',
            'total_capital': 2000,
            'shareholders': []
        }
        response = client.post('/company', json=data)
        assert response.status_code == 400
        assert response.json['message'] == 'Invalid total capital'

    def test_create_company_duplicate_name(self, client):
        company = Company(name='Test Company', registration_code='1234567', establishment_date='2020-01-01',
                          total_capital=5000)
        db.session.add(company)
        db.session.commit()
        data = {
            'name': 'Test Company',
            'registration_code': '7654321',
            'establishment_date': '2020-01-01',
            'total_capital': 5000,
            'shareholders': []
        }
        response = client.post('/company', json=data)
        assert response.status_code == 400
        assert response.json['message'] == 'Company with this name already exists'

    def test_create_company_duplicate_registration_code(self, client):
        company = Company(name='Test Company', registration_code='1234567', establishment_date='2020-01-01',
                          total_capital=5000)
        db.session.add(company)
        db.session.commit()
        data = {
            'name': 'Another Company',
            'registration_code': '1234567',
            'establishment_date': '2020-01-01',
            'total_capital': 5000,
            'shareholders': []
        }
        response = client.post('/company', json=data)
        assert response.status_code == 400
        assert response.json['message'] == 'Company with this registration code already exists'

    def test_create_company_invalid_shareholder_data(self, client):
        data = {
            'name': 'Test Company',
            'registration_code': '1234567',
            'establishment_date': '2020-01-01',
            'total_capital': 5000,
            'shareholders': [
                {
                    'type': 'individual',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'personal_code': 'invalid_code',
                    'share_amount': 5000
                }
            ]
        }
        response = client.post('/company', json=data)
        assert response.status_code == 400
        assert response.json['message'] == 'Invalid personal code'

    def test_create_company_total_shareholder_capital_mismatch(self, client):
        data = {
            'name': 'Test Company',
            'registration_code': '1234567',
            'establishment_date': '2020-01-01',
            'total_capital': 5000,
            'shareholders': [
                {
                    'type': 'individual',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'personal_code': '12345678901',
                    'share_amount': 3000
                }
            ]
        }
        response = client.post('/company', json=data)
        assert response.status_code == 400
        assert response.json['message'] == 'Total shareholder capital does not match company total capital'
