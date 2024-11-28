from ..repositories.app_repository import AppRepository
from ..models import Company
from ..validators import validate_company, validate_shareholder
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


engine = create_engine('postgresql://postgres:docker@flask_db:5432/rik')
Session = sessionmaker(bind=engine)


class AppService:

    @staticmethod
    def create_company(data):
        """
        Create a new company entity with shareholder entities.

        Name must be a unique string of 3-100 characters or numbers (including spaces).
        Registration code must be a unique 7-digit number.
        Establishment date must be less or equal to the current date and without time.
        Total capital must be an integer greater or equal to 2500.
        Total capital must be the sum of all shareholder share amounts.
        Shareholders added here will be marked as founders.

        Shareholder code (personal code for individuals, registration code for legal entities) must be unique.
        Shareholder share amount must be an integer greater or equal to 1.

        :param data: dict - Company data
        :raises ValueError: If the total shareholder capital does not match the company total capital
        :return: Company - The created company entity
        """
        new_company = Company(
            name=data['name'],
            registration_code=data['registration_code'],
            establishment_date=data['establishment_date'],
            total_capital=data['total_capital']
        )

        company_validation_response = validate_company(new_company)
        if company_validation_response.status_code != 200:
            return company_validation_response

        shareholders_data = data.get('shareholders', [])
        validated_shareholders = []
        total_shareholder_capital = 0

        for shareholder_data in shareholders_data:
            validate_shareholder_response = validate_shareholder(shareholder_data, new_company)
            validated_shareholders.append(validate_shareholder_response)
            total_shareholder_capital += validate_shareholder_response.share_amount

        if total_shareholder_capital != new_company.total_capital:
            raise ValueError('Total shareholder capital does not match company total capital')

        AppRepository.add(new_company)
        for shareholder in validated_shareholders:
            shareholder.company_id = new_company.id
            AppRepository.add_shareholder(shareholder)

        return new_company

    @staticmethod
    def get_company_by_registration_code(registration_code):
        return AppRepository.get_company_by_registration_code(registration_code)

    @staticmethod
    def get_all_companies():
        return AppRepository.get_all()

    @staticmethod
    def search_companies(name, registration_code, shareholder_name, shareholder_code, shareholder_type):
        return AppRepository.search_companies(
            name=name,
            registration_code=registration_code,
            shareholder_name=shareholder_name,
            shareholder_code=shareholder_code,
            shareholder_type=shareholder_type
        )

    @staticmethod
    def search_shareholder(query, limit, offset):
        return AppRepository.search_shareholder(query, limit, offset)

    @staticmethod
    def get_company_details(company_reg_code):
        """
        Get company details by registration code.
        Shareholders are sorted by share amount in descending order.

        :param company_reg_code: int - Company registration code
        :return: dict - Company entity, list of individual shareholders, list of legal entity shareholders
        """
        company = AppRepository.get_company_by_registration_code(company_reg_code)
        if not company:
            return None

        shareholders = AppRepository.get_company_shareholders(company.id)
        individual_shareholders = []
        legal_entity_shareholders = []

        for shareholder in shareholders:
            if shareholder.individual_id:
                individual = AppRepository.get_individual_by_id(shareholder.individual_id)
                individual_shareholders.append({
                    'first_name': individual.first_name,
                    'last_name': individual.last_name,
                    'personal_code': individual.personal_code,
                    'share_amount': shareholder.share_amount,
                    'is_founder': shareholder.is_founder
                })
            elif shareholder.legal_entity_id:
                legal_entity = AppRepository.get_legal_entity_by_id(shareholder.legal_entity_id)
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
        Update share amounts for shareholders of a company.
        The new share amount must be greater than or equal to the current share amount.
        The total capital of the company is updated accordingly.

        :param company_reg_code: int - Company registration code
        :param shareholders_data: list - List of dictionaries containing shareholder code, shareholder type etc.
        :raises ValueError: If the company is not found or the shareholder is not found
        :raises ValueError: If the new share amount is less than the current share amount
        :return: dict - A message indicating the success of the operation
        """
        session = Session()
        try:
            company = AppRepository.get_company_by_registration_code(company_reg_code)
            if company is None:
                raise ValueError('Company not found')

            total_capital_increase = 0

            for shareholder_data in shareholders_data:
                shareholder_code = shareholder_data['shareholder_code']
                shareholder_type = shareholder_data['shareholder_type']
                shareholder_id = AppRepository.get_shareholder_id_by_code(company.id, shareholder_code,
                                                                          shareholder_type,
                                                                          session)
                if shareholder_id is None:
                    raise ValueError('Shareholder not found')

                current_share_amount = shareholder_data['current_share_amount']
                new_share_amount = shareholder_data['new_share_amount']
                total_capital_increase += new_share_amount - current_share_amount

                if new_share_amount < current_share_amount:
                    raise ValueError('New share amount cannot be less than current share amount')

                AppRepository.update_share_amount(company.id, shareholder_id, new_share_amount, session)

            new_total_capital = company.total_capital + total_capital_increase
            AppRepository.update_total_capital(company.id, new_total_capital, session)

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

        :param data: dict - A dictionary containing shareholder details
        :raises ValueError: If the company is not found or the shareholder already exists
        :raises ValueError: If the shareholder is a legal entity with matching reg. code and already exists with a different name
        :raises ValueError: If the shareholder type is invalid
        :raises ValueError: If the individual or legal entity is already a shareholder in the company
        :raises SQLAlchemyError: If there is an error with the database operation
        :return: dict - A message indicating the success of the operation
        """
        session = Session()
        try:
            company_reg_code = data['company_reg_code']
            company = AppRepository.get_company_by_registration_code(company_reg_code)
            if not company:
                raise ValueError('Company not found')

            shareholder_type = data['shareholder_type']
            if shareholder_type == 'individual':
                shareholder_code = data['personal_code']
            elif shareholder_type == 'legal_entity':
                shareholder_code = data['registration_code']
                # Unlike individuals, legal entities can not share the same name
                existing_legal_entity = AppRepository.get_legal_entity_by_registration_code(shareholder_code)
                if existing_legal_entity is not None and existing_legal_entity.name != data['name']:
                    raise ValueError('Legal entity with this registration code already exists and has a different name')
            else:
                raise ValueError('Invalid shareholder type')

            if AppRepository.get_shareholder_id_by_code(company.id, shareholder_code, shareholder_type, session) is not None:
                raise ValueError('Shareholder already exists')

            new_shareholder = validate_shareholder(data, company, is_founder=False)

            AppRepository.add_shareholder(new_shareholder)
            AppRepository.update_total_capital(company.id, company.total_capital + new_shareholder.share_amount,
                                               session)

            session.commit()
            return {'message': 'Shareholder added successfully'}
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
