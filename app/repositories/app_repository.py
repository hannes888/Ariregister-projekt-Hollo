from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from ..models import Company, Shareholder, Individual, LegalEntity
from app.extensions import db
import logging

logger = logging.getLogger(__name__)


class AppRepository:
    @staticmethod
    def get_company_by_registration_code(registration_code):
        return Company.query.filter_by(registration_code=registration_code).one()

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
        total_shareholder_capital = db.session.query(db.func.sum(Shareholder.share_amount)).filter_by(
            company_id=company_id).scalar()
        if total_shareholder_capital != total_capital:
            raise ValueError('Total shareholder capital does not match company total capital')

    @staticmethod
    def search_companies(name=None, registration_code=None, shareholder_name=None, shareholder_code=None,
                         shareholder_type=None):
        """
        Search for companies by name, registration code, shareholder name, or shareholder code (personal/registration code).
        The search parameters can be combined to narrow down the search results.
        Searching by name implements case-insensitive fragment matching.
        Searching by any code requires an exact match.

        :param name: str - Company name
        :param registration_code: int - Company registration code
        :param shareholder_name: str - Shareholder name
        :param shareholder_code: int - Shareholder code
        :param shareholder_type: str - Shareholder type (individual or legal_entity)
        :return: dict - Matching companies
        """

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
                    shareholder_name_split = shareholder_name.split(' ')
                    for name in shareholder_name_split:
                        if name:
                            query = query.filter(
                                (Individual.first_name.ilike(f'%{name}%')) |
                                (Individual.last_name.ilike(f'%{name}%'))
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
        """
        Search for shareholders by individual first name, last name, or personal code,
        or legal entity name or registration code.
        Searching by name implements case-insensitive fragment matching.
        Searching by personal code or registration code requires an exact match.

        :param data: str - First name, last name, personal code, name, or registration code
        :param limit: int - Item limit per page
        :param offset: int - Page offset
        :return: dict - One page of search results and total result count
        """
        data = data.strip()
        if ' ' in data:
            first_part, last_part = data.rsplit(' ', 1)
            individual_query = Individual.query.filter(
                or_(
                    Individual.first_name.ilike(f'%{first_part}%'),
                    Individual.last_name.ilike(f'%{last_part}%')
                )
            )
        else:
            individual_query = Individual.query.filter(
                or_(
                    Individual.first_name.ilike(f'%{data}%'),
                    Individual.last_name.ilike(f'%{data}%'),
                    Individual.personal_code == data
                )
            )

        legal_entity_query = LegalEntity.query.filter(
            or_(
                LegalEntity.name.ilike(f'%{data}%'),
                LegalEntity.registration_code == data
            )
        )

        total_results = legal_entity_query.count() + individual_query.count()

        individual_results = individual_query.limit(limit).offset(offset).all()
        remaining_limit = limit - len(individual_results)
        legal_entity_offset = max(0, offset - individual_query.count())
        legal_entity_results = legal_entity_query.limit(remaining_limit).offset(legal_entity_offset).all()

        return {
            'results': individual_results + legal_entity_results,
            'total': total_results
        }

    @staticmethod
    def update_share_amount(company_id, shareholder_id, new_share_amount, session):
        """
        Update share amount for an existing shareholder.

        :param company_id: int - Company ID
        :param shareholder_id: int - Shareholder ID
        :param new_share_amount: int - New share amount
        :param session: SQLAlchemy session
        :return: None
        """
        try:
            shareholder = session.query(Shareholder).filter_by(company_id=company_id, id=shareholder_id).one()
            shareholder.share_amount = new_share_amount
            session.add(shareholder)
        except SQLAlchemyError as e:
            session.rollback()
            raise e

    @staticmethod
    def get_shareholder_id_by_code(company_id, shareholder_code, shareholder_type, session):
        """
        Get shareholder ID by code that can match either individual personal code or legal entity registration code.
        The shareholder must be associated with the specified company.

        :param company_id: int - Company ID
        :param shareholder_code: int - Shareholder code
        :param shareholder_type: str - Type of shareholder (individual or legal_entity)
        :param session: SQLAlchemy session
        :return: int - Shareholder ID
        """
        if shareholder_type == 'individual':
            individual = session.query(Individual).filter_by(personal_code=shareholder_code).first()
            if individual:
                shareholder = session.query(Shareholder).filter_by(company_id=company_id,
                                                                   individual_id=individual.id).first()
                return shareholder.id if shareholder else None
        elif shareholder_type == 'legal_entity':
            legal_entity = session.query(LegalEntity).filter_by(registration_code=shareholder_code).first()
            if legal_entity:
                shareholder = session.query(Shareholder).filter_by(company_id=company_id,
                                                                   legal_entity_id=legal_entity.id).first()
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
    def get_individual_by_personal_code(personal_code):
        return Individual.query.filter_by(personal_code=personal_code).one()

    @staticmethod
    def get_legal_entity_by_id(legal_entity_id):
        return LegalEntity.query.get(legal_entity_id)

    @staticmethod
    def get_legal_entity_by_registration_code(registration_code):
        return LegalEntity.query.filter_by(registration_code=registration_code).one()

    @staticmethod
    def get_shareholder_by_id(shareholder_id):
        return Shareholder.query.get(shareholder_id)
