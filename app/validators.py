import re
from datetime import datetime, date
from flask import make_response, jsonify
from app.extensions import db
from app.models import Shareholder, Individual, LegalEntity, Company

patterns = {
    'company_name': r'[a-zA-Z0-9]{3,100}',
    'registration_code': r'[0-9]{7}',
    'personal_id_number': r'[0-9]{11}',
    'registry_number': r'[0-9]{7}'
}


def validate_company_name(input_value):
    pattern = patterns.get('company_name')
    if pattern and re.match(pattern, input_value):
        return True
    return False


def validate_registration_code(input_value):
    pattern = patterns.get('registration_code')
    if pattern and re.match(pattern, input_value):
        return True
    return False


def validate_establishment_date(input_value):
    input_date = datetime.strptime(input_value, '%Y-%m-%d').date()
    today = date.today()
    return input_date <= today


def validate_total_capital(input_value):
    return isinstance(input_value, int) and input_value >= 2500


def validate_personal_id_number(input_value):
    pattern = patterns.get('personal_id_number')
    if pattern and re.match(pattern, input_value):
        return True
    return False


def validate_registry_number(input_value):
    pattern = patterns.get('registry_number')
    if pattern and re.match(pattern, input_value):
        return True
    return False


def validate_shareholder(shareholder_data, company, is_founder=True):
    """
    Validate shareholder data and create a new Shareholder instance.

    Shareholder share amount must be an integer greater than 0.
    Individual shareholders must have first name, last name, and personal code.
    Legal entity shareholders must have name and registration code.
    Shareholder personal code must be a valid Estonian personal ID number.
    Shareholder registration code must be a valid Estonian registry number.
    Shareholder registration code must be unique.

    If the shareholder code matches an existing individual or legal entity, the existing instance is used, regardless of the provided name.

    :param shareholder_data: Shareholder data
    :param company: Company instance
    :param is_founder: bool - Whether the shareholder is a company founder
    :raises ValueError: If shareholder type is invalid
    :return: Shareholder instance
    """
    if int(shareholder_data.get('share_amount')) < 1:
        return make_response(jsonify({'message': 'Invalid share amount'}), 400)

    shareholder_type = shareholder_data.get('shareholder_type')

    if shareholder_type == 'individual':
        required_fields = ['first_name', 'last_name', 'personal_code']
        for field in required_fields:
            if not shareholder_data.get(field):
                return make_response(jsonify({'message': f'Missing field: {field}'}), 400)

        individual_data = {
            'first_name': shareholder_data['first_name'],
            'last_name': shareholder_data['last_name'],
            'personal_code': shareholder_data['personal_code']
        }

        if not validate_personal_id_number(individual_data['personal_code']):
            return make_response(jsonify({'message': 'Invalid personal code'}), 400)

        individual = Individual.query.filter_by(personal_code=individual_data['personal_code']).first()
        if not individual:
            individual = Individual(**individual_data)
            db.session.add(individual)
            db.session.flush()  # Ensure individual.id is available

        shareholder = Shareholder(
            company_id=company.id,
            individual_id=individual.id,
            share_amount=shareholder_data['share_amount'],
            is_founder=is_founder
        )
    elif shareholder_type == 'legal_entity':
        required_fields = ['name', 'registration_code']
        for field in required_fields:
            if not shareholder_data.get(field):
                return make_response(jsonify({'message': f'Missing field: {field}'}), 400)

        legal_entity_data = {
            'name': shareholder_data['name'],
            'registration_code': shareholder_data['registration_code']
        }

        if not validate_registry_number(legal_entity_data['registration_code']):
            return make_response(jsonify({'message': 'Invalid registration code'}), 400)

        legal_entity = LegalEntity.query.filter_by(registration_code=legal_entity_data['registration_code']).first()
        if not legal_entity:
            legal_entity = LegalEntity(**legal_entity_data)
            db.session.add(legal_entity)
            db.session.flush()  # Ensure legal_entity.id is available

        shareholder = Shareholder(
            company_id=company.id,
            legal_entity_id=legal_entity.id,
            share_amount=shareholder_data['share_amount'],
            is_founder=is_founder
        )
    else:
        raise ValueError('Invalid shareholder data')

    return shareholder


def validate_company(company):
    if not validate_company_name(company.name):
        return make_response(jsonify({'message': 'Invalid company name'}), 400)

    if not validate_registration_code(company.registration_code):
        return make_response(jsonify({'message': 'Invalid registration code'}), 400)

    if not validate_establishment_date(company.establishment_date):
        return make_response(jsonify({'message': 'Invalid establishment date'}), 400)

    if not validate_total_capital(company.total_capital):
        return make_response(jsonify({'message': 'Invalid total capital'}), 400)

    if Company.query.filter_by(registration_code=company.registration_code).first():
        return make_response(jsonify({'message': 'Company with this registration code already exists'}), 400)

    if Company.query.filter_by(name=company.name).first():
        return make_response(jsonify({'message': 'Company with this name already exists'}), 400)

    return make_response(jsonify({'message': 'Company validated'}), 200)
