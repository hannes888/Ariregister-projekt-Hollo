# app/repositories/company_repository.py
from sqlalchemy.exc import SQLAlchemyError

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
    def search_shareholder(data=None, limit=5, offset=0):
        individual_query = Individual.query.filter(
            (Individual.first_name.ilike(f'%{data}%')) |
            (Individual.last_name.ilike(f'%{data}%')) |
            (Individual.personal_code == data)
        )
        legal_entity_query = LegalEntity.query.filter(
            (LegalEntity.name.ilike(f'%{data}%')) |
            (LegalEntity.registration_code == data)
        )

        total_results = legal_entity_query.count() + individual_query.count()

        individual_results = individual_query.limit(limit).offset(offset).all()
        remaining_limit = limit - len(individual_results)
        legal_entity_results = legal_entity_query.limit(remaining_limit).offset(offset).all()

        return {
            'results': individual_results + legal_entity_results,
            'total': total_results
        }

    @staticmethod
    def update_share_amount(shareholder_id, new_share_amount, session):
        try:
            shareholder = session.query(Shareholder).filter_by(id=shareholder_id).one()
            shareholder.share_amount = new_share_amount
            session.add(shareholder)
        except SQLAlchemyError as e:
            session.rollback()
            raise e

    @staticmethod
    def get_shareholder_id_by_code(shareholder_code, shareholder_type, session):
        if shareholder_type == 'individual':
            individual = session.query(Individual).filter_by(personal_code=shareholder_code).first()
            if individual:
                shareholder = session.query(Shareholder).filter_by(individual_id=individual.id).first()
                return shareholder.id if shareholder else None
        elif shareholder_type == 'legal_entity':
            legal_entity = session.query(LegalEntity).filter_by(registration_code=shareholder_code).first()
            if legal_entity:
                shareholder = session.query(Shareholder).filter_by(legal_entity_id=legal_entity.id).first()
                return shareholder.id if shareholder else None
        return None

    @staticmethod
    def update_total_capital(company_id, new_total_capital, session):
        company = session.query(Company).get(company_id)
        company.total_capital = new_total_capital
        session.add(company)

    @staticmethod
    def get_company_shareholders(company_id):
        return Shareholder.query.filter_by(company_id=company_id).all()

    @staticmethod
    def get_individual_by_id(individual_id):
        return Individual.query.get(individual_id)

    @staticmethod
    def get_legal_entity_by_id(legal_entity_id):
        return LegalEntity.query.get(legal_entity_id)