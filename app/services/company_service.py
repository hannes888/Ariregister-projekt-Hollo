# app/services/company_service.py
from .. import db
from ..repositories.company_repository import CompanyRepository
from ..models import Company, Shareholder, Individual, LegalEntity
from ..validators import validate_company, validate_shareholder
from sqlalchemy.exc import SQLAlchemyError


class CompanyService:
    @staticmethod
    def create_company(data):
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
