from flask import request, jsonify, make_response, current_app as app, render_template
from . import db
from .models import Company, Individual, LegalEntity, Shareholder
from .validators import *


# Default route
@app.route('/')
def index():
    return render_template('index.html')


# Company routes
@app.route('/company/<string:company_reg_code>')
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


@app.route('/company', methods=['POST'])
def create_company():
    try:
        data = request.get_json()
        app.logger.debug(f"Received data: {data}")

        # establishment_date = datetime.strptime(data['establishment_date'], '%Y-%m-%d').date()

        new_company = Company(
            name=data['name'],
            registration_code=data['registration_code'],
            establishment_date=data['establishment_date'],
            total_capital=data['total_capital']
        )

        total_shareholder_capital = 0

        # Validate company data
        if not validate_company_name(new_company.name):
            return make_response(jsonify({'message': 'Invalid company name'}), 400)
        if not validate_registration_code(new_company.registration_code):
            return make_response(jsonify({'message': 'Invalid registration code'}), 400)
        if not validate_establishment_date(new_company.establishment_date):
            return make_response(jsonify({'message': 'Invalid establishment date'}), 400)
        if not validate_total_capital(new_company.total_capital):
            return make_response(jsonify({'message': 'Invalid total capital'}), 400)
        if Company.query.filter_by(registration_code=new_company.registration_code).first():
            return make_response(jsonify({'message': 'Company with this registration code already exists'}), 400)
        if Company.query.filter_by(name=new_company.name).first():
            return make_response(jsonify({'message': 'Company with this name already exists'}), 400)

        db.session.add(new_company)

        # Add shareholders
        shareholders_data = data.get('shareholders', [])
        for shareholder_data in shareholders_data:
            app.logger.debug(f"Processing shareholder: {shareholder_data}")

            # Validate shareholder data
            if shareholder_data['share_amount'] <= 1 or not isinstance(shareholder_data['share_amount'], int):
                return make_response(jsonify({'message': 'Invalid share amount'}), 400)

            if shareholder_data['type'] == 'individual':
                new_individual = Individual(
                    first_name=shareholder_data['first_name'],
                    last_name=shareholder_data['last_name'],
                    personal_code=shareholder_data['personal_code']
                )

                # Validate individual data
                if not validate_personal_id_number(new_individual.personal_code):
                    return make_response(jsonify({'message': 'Invalid personal code'}), 400)

                existing_individual = Individual.query.filter_by(personal_code=new_individual.personal_code).first()
                if existing_individual:
                    new_individual = existing_individual
                else:
                    db.session.add(new_individual)

                shareholder = Shareholder(
                    company_id=new_company.id,
                    individual_id=new_individual.id,
                    share_amount=shareholder_data['share_amount'],
                    is_founder=True
                )
            elif shareholder_data['type'] == 'legal_entity':
                new_legal_entity = LegalEntity(
                    name=shareholder_data['name'],
                    registration_code=shareholder_data['registration_code']
                )

                # Validate legal entity data
                if not validate_registry_number(new_legal_entity.registration_code):
                    return make_response(jsonify({'message': 'Invalid registry number'}), 400)

                existing_legal_entity = LegalEntity.query.filter_by(registration_code=new_legal_entity.registration_code).first()
                if existing_legal_entity:
                    new_legal_entity = existing_legal_entity
                else:
                    db.session.add(new_legal_entity)

                shareholder = Shareholder(
                    company_id=new_company.id,
                    legal_entity_id=new_legal_entity.id,
                    share_amount=shareholder_data['share_amount'],
                    is_founder=True
                )
            else:
                return make_response(jsonify({'message': 'Invalid shareholder type'}), 400)
            db.session.add(shareholder)
            total_shareholder_capital += shareholder.share_amount

        # Validate total shareholder capital
        if total_shareholder_capital != new_company.total_capital:
            return make_response(jsonify({'message': 'Total shareholder capital does not match company total capital'}), 400)

        db.session.commit()

        return make_response(jsonify({'message': 'Company and shareholders created'}), 201)
    except Exception as e:
        app.logger.error(f"Error creating company: {e}")
        return make_response(jsonify({'message': f'Error creating company {e}'}), 500)


@app.route('/search', methods=['GET'])
def search_companies():
    try:
        name = request.args.get('name')
        registration_code = request.args.get('registration_code')
        shareholder_name = request.args.get('shareholder_name')
        shareholder_code = request.args.get('shareholder_code')

        query = db.session.query(Company)

        if name:
            query = query.filter(Company.name.ilike(f'%{name}%'))
        if registration_code:
            query = query.filter(Company.registration_code.ilike(f'%{registration_code}%'))
        if shareholder_name or shareholder_code:
            query = query.join(Shareholder)
            if shareholder_name:
                query = query.join(Individual).filter(
                    (Individual.first_name.ilike(f'%{shareholder_name}%')) |
                    (Individual.last_name.ilike(f'%{shareholder_name}%'))
                )
            if shareholder_code:
                query = query.join(Individual).filter(Individual.personal_code.ilike(f'%{shareholder_code}%'))

        companies = query.all()

        results = []
        for company in companies:
            results.append({
                'name': company.name,
                'registration_code': company.registration_code,
                'id': company.id
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
