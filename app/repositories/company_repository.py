# app/repositories/company_repository.py
from ..models import Company, Shareholder, Individual, LegalEntity
from .. import db


class CompanyRepository:
    @staticmethod
    def get_by_registration_code(registration_code):
        return Company.query.filter_by(registration_code=registration_code).first()

    @staticmethod
    def add(company):
        db.session.add(company)
        db.session.commit()

    @staticmethod
    def add_shareholder(shareholder):
        db.session.add(shareholder)
        db.session.commit()

    @staticmethod
    def get_all():
        return Company.query.all()

    @staticmethod
    def validate_total_shareholder_capital(company_id, total_capital):
        total_shareholder_capital = db.session.query(db.func.sum(Shareholder.share_amount)).filter_by(company_id=company_id).scalar()
        if total_shareholder_capital != total_capital:
            raise ValueError('Total shareholder capital does not match company total capital')

    @staticmethod
    def search_companies(name=None, registration_code=None, shareholder_name=None, shareholder_code=None, shareholder_type=None):
        query = db.session.query(Company)

        if name:
            query = query.filter(Company.name.ilike(f'%{name}%'))
        if registration_code:
            query = query.filter(Company.registration_code == registration_code)

        if shareholder_name or shareholder_code:
            query = query.join(Shareholder)
            if shareholder_type == 'individual':
                query = query.join(Individual)
                if shareholder_name:
                    query = query.filter(
                        (Individual.first_name.ilike(f'%{shareholder_name}%')) |
                        (Individual.last_name.ilike(f'%{shareholder_name}%'))
                    )
                if shareholder_code:
                    query = query.filter(Individual.personal_code == shareholder_code)
            elif shareholder_type == 'legal_entity':
                query = query.join(LegalEntity)
                if shareholder_code:
                    query = query.filter(LegalEntity.registration_code == shareholder_code)
                if shareholder_name:
                    query = query.filter(LegalEntity.name.ilike(f'%{shareholder_name}%'))

        return query.all()

    @staticmethod
    def search_shareholder(data=None):

        individual_results = Individual.query.filter(
            (Individual.first_name.ilike(f'%{data}%')) |
            (Individual.last_name.ilike(f'%{data}%')) |
            (Individual.personal_code == data)
        ).all()
        legal_entity_results = LegalEntity.query.filter(
            (LegalEntity.name.ilike(f'%{data}%')) |
            (LegalEntity.registration_code == data)
        ).all()

        return individual_results + legal_entity_results
