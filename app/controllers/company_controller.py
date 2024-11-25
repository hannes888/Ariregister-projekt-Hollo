# app/controllers/company_controller.py
from flask import Blueprint, request, jsonify, make_response, current_app as app, render_template
from ..services.company_service import CompanyService
from ..models import Shareholder, LegalEntity, Individual
from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint('company', __name__)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/view-company/<string:company_reg_code>')
def view_company(company_reg_code):
    company = CompanyService.get_company_by_registration_code(company_reg_code)
    if not company:
        return make_response(jsonify({'message': 'Company not found'}), 404)
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


@bp.route('/create-company', methods=['GET'])
def create_company_form():
    return render_template('create-company.html')


@bp.route('/create-company', methods=['POST'])
def create_company():
    try:
        data = request.get_json()
        new_company = CompanyService.create_company(data)
        return make_response(jsonify({'message': 'Company and shareholders created', 'company_reg_num': new_company.registration_code}), 201)
    except ValueError as e:
        return make_response(jsonify({'message': f'Error creating company: {e}'}), 400)
    except Exception as e:
        return make_response(jsonify({'message': f'Unexpected error: {e}'}), 500)


@bp.route('/search', methods=['GET'])
def search_companies():
    try:
        name = request.args.get('name')
        registration_code = request.args.get('registration_code')
        shareholder_name = request.args.get('shareholder_name')
        shareholder_code = request.args.get('shareholder_code')
        shareholder_type = request.args.get('shareholder_type')

        companies = CompanyService.search_companies(name, registration_code, shareholder_name, shareholder_code, shareholder_type)

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


@app.route('/search-shareholder', methods=['GET'])
def search_shareholder():
    try:
        query = request.args.get('query')
        limit = int(request.args.get('limit', 5))
        offset = int(request.args.get('offset', 0))
        result_data = CompanyService.search_shareholder(query, limit, offset)

        serialized_results = []
        for result in result_data['results']:
            if isinstance(result, Individual):
                serialized_results.append({
                    'type': 'individual',
                    'first_name': result.first_name,
                    'last_name': result.last_name,
                    'personal_code': result.personal_code
                })
            elif isinstance(result, LegalEntity):
                serialized_results.append({
                    'type': 'legal_entity',
                    'name': result.name,
                    'registration_code': result.registration_code
                })

        return jsonify({
            'results': serialized_results,
            'total': result_data['total']
        })
    except Exception as e:
        app.logger.error(f"Error searching shareholders: {e}")
        return make_response(jsonify({'message': 'Error searching shareholders'}), 500)