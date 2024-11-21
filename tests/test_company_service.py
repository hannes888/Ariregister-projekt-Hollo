# test_company_service.py
import unittest
from unittest.mock import patch, MagicMock
from app.services.company_service import CompanyService
from app.models import Company, Shareholder


class TestCompanyService(unittest.TestCase):

    @patch('app.services.company_service.CompanyRepository')
    @patch('app.services.company_service.validate_company')
    @patch('app.services.company_service.validate_shareholder')
    def test_create_company_success(self, mock_validate_shareholder, mock_validate_company, mock_company_repository):
        # Mock data
        data = {
            'name': 'Test Company',
            'registration_code': '1234567',
            'establishment_date': '2023-01-01',
            'total_capital': 5000,
            'shareholders': [
                {
                    "type": "individual",
                    "first_name": "John",
                    "last_name": "Doe",
                    "personal_code": "12345678901",
                    "share_amount": 2500,
                },
                {
                    "type": "legal_entity",
                    "name": "Examples Legal Entity01",
                    "registration_code": "1234567",
                    "share_amount": 2500,
                }
            ]
        }

        # Mock validation responses
        mock_validate_company.return_value = MagicMock(status_code=200)
        mock_validate_shareholder.side_effect = [
            Shareholder(individual_id=1, share_amount=2500),
            Shareholder(legal_entity_id=1, share_amount=2500)
        ]

        # Call the method
        new_company = CompanyService.create_company(data)

        # Assertions
        mock_company_repository.add.assert_called_once_with(new_company)
        self.assertEqual(new_company.name, 'Test Company')
        self.assertEqual(new_company.registration_code, '1234567')
        self.assertEqual(new_company.total_capital, 5000)

    @patch('app.services.company_service.CompanyRepository')
    @patch('app.services.company_service.validate_company')
    @patch('app.services.company_service.validate_shareholder')
    def test_create_company_validation_failure(self, mock_validate_shareholder, mock_validate_company, mock_company_repository):
        # Mock data
        data = {
            'name': 'Test Company',
            'registration_code': '123456',
            'establishment_date': '2023-01-01',
            'total_capital': 1000,
            'shareholders': [
                {'name': 'John Doe', 'share_amount': 500},
                {'name': 'Jane Doe', 'share_amount': 500}
            ]
        }

        # Mock validation responses
        mock_validate_company.return_value = MagicMock(status_code=400, message='Invalid company data')

        # Call the method
        response = CompanyService.create_company(data)

        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.message, 'Invalid company data')
        mock_company_repository.add.assert_not_called()

    @patch('app.services.company_service.CompanyRepository')
    @patch('app.services.company_service.validate_company')
    @patch('app.services.company_service.validate_shareholder')
    def test_create_company_shareholder_validation_failure(self, mock_validate_shareholder, mock_validate_company, mock_company_repository):
        # Mock data
        data = {
            'name': 'Test Company',
            'registration_code': '123456',
            'establishment_date': '2023-01-01',
            'total_capital': 1000,
            'shareholders': [
                {'name': 'John Doe', 'share_amount': 500},
                {'name': 'Jane Doe', 'share_amount': 500}
            ]
        }

        # Mock validation responses
        mock_validate_company.return_value = MagicMock(status_code=200)
        mock_validate_shareholder.side_effect = ValueError('Invalid shareholder data')

        # Call the method
        with self.assertRaises(ValueError) as context:
            CompanyService.create_company(data)

        # Assertions
        self.assertEqual(str(context.exception), 'Invalid shareholder data')
        mock_company_repository.add.assert_not_called()


if __name__ == '__main__':
    unittest.main()