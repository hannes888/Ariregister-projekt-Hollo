# app/services/company_service.py
import logging
from .. import db
from ..repositories.company_repository import CompanyRepository
from ..models import Company, Shareholder, Individual, LegalEntity
from ..validators import validate_company, validate_shareholder
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_engine('postgresql://postgres:docker@flask_db:5432/rik')
Session = sessionmaker(bind=engine)


class CompanyService:

    @staticmethod
    def create_company(data):
        """
        Create a new company entity with shareholder entities.
        :param data:
        :return:
        """
        new_company = Company(
            name=data['name'],
            registration_code=data['registration_code'],
            establishment_date=data['establishment_date'],
            total_capital=data['total_capital']
        )

        # Validate company data
        company_validation_response = validate_company(new_company)
        if company_validation_response.status_code != 200:
            return company_validation_response

        # Validate shareholders
        shareholders_data = data.get('shareholders', [])
        validated_shareholders = []
        total_shareholder_capital = 0

        for shareholder_data in shareholders_data:
            validate_shareholder_response = validate_shareholder(shareholder_data, new_company)
            validated_shareholders.append(validate_shareholder_response)
            total_shareholder_capital += validate_shareholder_response.share_amount

        # Validate total shareholder capital
        if total_shareholder_capital != new_company.total_capital:
            raise ValueError('Total shareholder capital does not match company total capital')

        # Add company and shareholders using repository
        CompanyRepository.add(new_company)
        for shareholder in validated_shareholders:
            shareholder.company_id = new_company.id
            CompanyRepository.add_shareholder(shareholder)

        return new_company

    @staticmethod
    def get_company_by_registration_code(registration_code):
        return CompanyRepository.get_by_registration_code(registration_code)

    @staticmethod
    def get_all_companies():
        return CompanyRepository.get_all()

    @staticmethod
    def search_companies(name, registration_code, shareholder_name, shareholder_code, shareholder_type):
        return CompanyRepository.search_companies(
            name=name,
            registration_code=registration_code,
            shareholder_name=shareholder_name,
            shareholder_code=shareholder_code,
            shareholder_type=shareholder_type
        )

    @staticmethod
    def search_shareholder(query, limit, offset):
        return CompanyRepository.search_shareholder(query, limit, offset)

    @staticmethod
    def get_company_details(company_reg_code):
        """
        Get company details by registration code
        :param company_reg_code: Company registration code
        :return: Company entity, list of individual shareholders, list of legal entity shareholders
        """
        company = CompanyRepository.get_by_registration_code(company_reg_code)
        if not company:
            return None

        shareholders = CompanyRepository.get_company_shareholders(company.id)
        individual_shareholders = []
        legal_entity_shareholders = []

        for shareholder in shareholders:
            if shareholder.individual_id:
                individual = CompanyRepository.get_individual_by_id(shareholder.individual_id)
                individual_shareholders.append({
                    'first_name': individual.first_name,
                    'last_name': individual.last_name,
                    'personal_code': individual.personal_code,
                    'share_amount': shareholder.share_amount,
                    'is_founder': shareholder.is_founder
                })
            elif shareholder.legal_entity_id:
                legal_entity = CompanyRepository.get_legal_entity_by_id(shareholder.legal_entity_id)
                legal_entity_shareholders.append({
                    'name': legal_entity.name,
                    'registration_code': legal_entity.registration_code,
                    'share_amount': shareholder.share_amount,
                    'is_founder': shareholder.is_founder
                })

        # Sort shareholders by share_amount in descending order
        individual_shareholders.sort(key=lambda x: x['share_amount'], reverse=True)
        legal_entity_shareholders.sort(key=lambda x: x['share_amount'], reverse=True)

        return {
            'company': company,
            'individual_shareholders': individual_shareholders,
            'legal_entity_shareholders': legal_entity_shareholders
        }

    @staticmethod
    def update_share_amount(company_reg_code, shareholders_data):
        """
        Update share amounts for shareholders of a company
        :param company_reg_code:
        :param shareholders_data:
        :return:
        """
        session = Session()
        try:
            company = CompanyRepository.get_by_registration_code(company_reg_code)
            if company is None:
                raise ValueError('Company not found')

            total_capital_increase = 0

            for shareholder_data in shareholders_data:
                logger.error(
                    f"Updating share amount in service layer for shareholder {shareholder_data['shareholder_code']} with company reg code {company_reg_code}")
                shareholder_code = shareholder_data['shareholder_code']
                shareholder_type = shareholder_data['shareholder_type']
                shareholder_id = CompanyRepository.get_shareholder_id_by_code(company.id, shareholder_code,
                                                                              shareholder_type,
                                                                              session)
                if shareholder_id is None:
                    raise ValueError('Shareholder not found')

                current_share_amount = shareholder_data['current_share_amount']
                new_share_amount = shareholder_data['new_share_amount']
                total_capital_increase += new_share_amount - current_share_amount

                if new_share_amount < current_share_amount:
                    raise ValueError('New share amount cannot be less than current share amount')

                CompanyRepository.update_share_amount(company.id, shareholder_id, new_share_amount, session)

            new_total_capital = company.total_capital + total_capital_increase
            CompanyRepository.update_total_capital(company.id, new_total_capital, session)

            session.commit()
            return {'message': 'Share amounts updated successfully'}
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def add_shareholder(data):
        """
        Adds a new shareholder to the company.

        :param data: A dictionary containing shareholder details.
        :type data: dict
        :raises ValueError: If the company is not found or the shareholder already exists.
        :raises SQLAlchemyError: If there is an error with the database operation.
        :return: A message indicating the success of the operation.
        :rtype: dict
        """
        session = Session()
        try:
            company_reg_code = data['company_reg_code']
            company = CompanyRepository.get_by_registration_code(company_reg_code)
            if not company:
                raise ValueError('Company not found')

            shareholder_code = data['registration_code']
            shareholder_type = data['shareholder_type']

            if not CompanyRepository.get_shareholder_id_by_code(company.id, shareholder_code, shareholder_type, session):
                raise ValueError('Shareholder already exists')

            new_shareholder = validate_shareholder(data, company, is_founder=False)
            logger.info(f"Adding shareholder {new_shareholder}")

            CompanyRepository.add_shareholder(new_shareholder)
            CompanyRepository.update_total_capital(company.id, company.total_capital + new_shareholder.share_amount,
                                                   session)

            session.commit()
            return {'message': 'Shareholder added successfully'}
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding shareholder: {e}")
            raise e
        finally:
            session.close()
