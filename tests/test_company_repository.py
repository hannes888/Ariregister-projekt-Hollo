import unittest
from app import create_app, db
from app.models import Individual, LegalEntity
from app.repositories.company_repository import CompanyRepository


class SearchShareholderTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Add test data
        self.individual1 = Individual(first_name='John', last_name='Doe', personal_code='123456789')
        self.individual2 = Individual(first_name='Jane', last_name='Smith', personal_code='987654321')
        self.legal_entity1 = LegalEntity(name='Acme Corp', registration_code='AC123')
        self.legal_entity2 = LegalEntity(name='Globex Inc', registration_code='GI456')
        db.session.add_all([self.individual1, self.individual2, self.legal_entity1, self.legal_entity2])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_search_individuals(self):
        result = CompanyRepository.search_shareholder(data='John', limit=5, offset=0)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0].first_name, 'John')

    def test_search_legal_entities(self):
        result = CompanyRepository.search_shareholder(data='Acme', limit=5, offset=0)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0].name, 'Acme Corp')

    def test_search_pagination(self):
        result = CompanyRepository.search_shareholder(data='', limit=1, offset=0)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['total'], 4)

        result = CompanyRepository.search_shareholder(data='', limit=1, offset=1)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['total'], 4)


if __name__ == '__main__':
    unittest.main()
