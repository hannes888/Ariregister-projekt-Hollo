import re
from datetime import datetime, date

patterns = {
    'company_name': r'[a-zA-Z0-9]{3,100}',
    'registration_code': r'[0-9]{7}',
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
    return isinstance(input_value, int) and input_value > 2500
