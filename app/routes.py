from flask import request, jsonify, make_response, current_app as app
from . import db
from .models import Company, Individual, LegalEntity, Shareholder
from .validators import validate_company_name, validate_registration_code, validate_establishment_date, \
    validate_total_capital


# Company routes

@app.route('/company', methods=['POST'])
def create_company():
    try:
        data = request.get_json()
        app.logger.debug(f"Received data: {data}")

        new_company = Company(
            name=data['name'],
            registration_code=data['registration_code'],
            establishment_date=data['establishment_date'],
            total_capital=data['total_capital']
        )

        # Validate input data
        if not validate_company_name(new_company.name):
            return make_response(jsonify({'message': 'Invalid company name'}), 400)
        if not validate_registration_code(new_company.registration_code):
            return make_response(jsonify({'message': 'Invalid registration code'}), 400)
        if not validate_establishment_date(new_company.establishment_date):
            return make_response(jsonify({'message': 'Invalid establishment date'}), 400)
        if not validate_total_capital(new_company.total_capital):
            return make_response(jsonify({'message': 'Invalid total capital'}), 400)

        db.session.add(new_company)
        db.session.commit()

        # Add shareholders
        shareholders_data = data.get('shareholders', [])
        for shareholder_data in shareholders_data:
            app.logger.debug(f"Processing shareholder: {shareholder_data}")
            if shareholder_data['type'] == 'individual':
                new_individual = Individual(
                    first_name=shareholder_data['first_name'],
                    last_name=shareholder_data['last_name'],
                    personal_code=shareholder_data['personal_code']
                )
                db.session.add(new_individual)
                db.session.commit()  # Commit to generate the ID
                shareholder = Shareholder(
                    company_id=new_company.id,
                    individual_id=new_individual.id,
                    share_amount=shareholder_data['share_amount'],
                    is_founder=shareholder_data.get('is_founder', False)
                )
            elif shareholder_data['type'] == 'legal_entity':
                new_legal_entity = LegalEntity(
                    name=shareholder_data['name'],
                    registration_code=shareholder_data['registration_code']
                )
                db.session.add(new_legal_entity)
                db.session.commit()  # Commit to generate the ID
                shareholder = Shareholder(
                    company_id=new_company.id,
                    legal_entity_id=new_legal_entity.id,
                    share_amount=shareholder_data['share_amount'],
                    is_founder=shareholder_data.get('is_founder', False)
                )
            else:
                return make_response(jsonify({'message': 'Invalid shareholder type'}), 400)
            db.session.add(shareholder)

        db.session.commit()
        return make_response(jsonify({'message': 'Company and shareholders created'}), 201)
    except Exception as e:
        app.logger.error(f"Error creating company: {e}")
        return make_response(jsonify({'message': 'Error creating company'}), 500)


@app.route('/company/<int:company_id>', methods=['GET'])
def get_company(company_id):
    company = Company.query.get(company_id)
    if company:
        return make_response(jsonify({
            'name': company.name,
            'registration_code': company.registration_code,
            'establishment_date': company.establishment_date,
            'total_capital': company.total_capital
        }), 200)
    return make_response(jsonify({'message': 'Company not found'}), 404)


@app.route('/legal-entity', methods=['POST'])
def create_legal_entity():
    try:
        data = request.get_json()
        new_legal_entity = LegalEntity(name=data['name'], registration_code=data['registration_code'])
        db.session.add(new_legal_entity)
        db.session.commit()
        return make_response(jsonify({'message': 'Legal entity created'}), 201)
    except Exception as e:
        app.logger.error(f"Error creating legal entity: {e}")
        return make_response(jsonify({'message': 'Error creating legal entity'}), 500)
