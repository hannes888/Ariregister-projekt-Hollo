from flask import request, jsonify, make_response, current_app as app, render_template
from . import db
from .models import Company, Individual, LegalEntity, Shareholder
from .validators import *
from sqlalchemy.exc import SQLAlchemyError


# Default route
@app.route('/')
def index():
    return render_template('index.html')


# Company routes
@app.route('/view-company/<string:company_reg_code>')
def view_company(company_reg_code):
    company = Company.query.filter_by(registration_code=company_reg_code).first_or_404()
    shareholders = Shareholder.query.filter_by(company_id=company.id).all()

    individual_shareholders = []
    legal_entity_shareholders = []

    for shareholder in shareholders:
        if shareholder.individual_id:
            individual = Individual.query.get(shareholder.individual_id)
            individual_shareholders.append({
                'first_name': individual.first_name,
                'last_name': individual.last_name,
                'personal_code': individual.personal_code,
                'share_amount': shareholder.share_amount,
                'is_founder': shareholder.is_founder
            })
        elif shareholder.legal_entity_id:
            legal_entity = LegalEntity.query.get(shareholder.legal_entity_id)
            legal_entity_shareholders.append({
                'name': legal_entity.name,
                'registration_code': legal_entity.registration_code,
                'share_amount': shareholder.share_amount,
                'is_founder': shareholder.is_founder
            })

    return render_template(
        'view-company.html',
        company=company,
        individual_shareholders=individual_shareholders,
        legal_entity_shareholders=legal_entity_shareholders
    )


@app.route('/create-company', methods=['GET'])
def create_company_form():
    return render_template('create-company.html')


@app.route('/create-company', methods=['POST'])
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

        # Validate company data
        company_validation_response = validate_company(new_company)
        if company_validation_response.status_code != 200:
            return company_validation_response

        total_shareholder_capital = 0

        # Start a transaction
        db.session.add(new_company)
        db.session.flush()  # Ensure new_company.id is available
        print(f"New company id: {new_company.id}")

        # Add shareholders
        shareholders_data = data.get('shareholders', [])
        for shareholder_data in shareholders_data:
            validate_shareholder_response = validate_shareholder(shareholder_data, new_company)
            db.session.add(validate_shareholder_response)
            total_shareholder_capital += validate_shareholder_response.share_amount

        # Validate total shareholder capital
        if total_shareholder_capital != new_company.total_capital:
            raise ValueError('Total shareholder capital does not match company total capital')

        db.session.commit()
        return make_response(jsonify({'message': 'Company and shareholders created', 'company_reg_num': new_company.registration_code}), 201)
    except (ValueError, SQLAlchemyError) as e:
        db.session.rollback()
        app.logger.error(f"Error creating company: {e}")
        return make_response(jsonify({'message': f'Error creating company: {e}'}), 400)
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        return make_response(jsonify({'message': f'Unexpected error: {e}'}), 500)


@app.route('/search', methods=['GET'])
def search_companies():
    try:
        name = request.args.get('name')
        registration_code = request.args.get('registration_code')
        shareholder_name = request.args.get('shareholder_name')
        shareholder_code = request.args.get('shareholder_code')
        shareholder_type = request.args.get('shareholder_type')

        query = db.session.query(Company)

        if name:
            query = query.filter(Company.name.ilike(f'%{name}%'))
        if registration_code:
            query = query.filter(Company.registration_code == registration_code)

        if shareholder_name or shareholder_code or shareholder_type:
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

        companies = query.all()

        results = []
        for company in companies:
            results.append({
                'name': company.name,
                'registry_code': company.registration_code,
                'id': company.id  # TODO: Remove?
            })

        return make_response(jsonify(results), 200)
    except Exception as e:
        app.logger.error(f"Error searching companies: {e}")
        return make_response(jsonify({'message': 'Error searching companies'}), 500)


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
