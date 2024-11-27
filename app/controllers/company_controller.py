from flask import Blueprint, request, jsonify, make_response, current_app as app, render_template
from ..services.app_service import AppService

company_bp = Blueprint('company', __name__)


@company_bp.route('/')
def index():
    return render_template('index.html')


@company_bp.route('/view-company/<string:company_reg_code>')
def view_company(company_reg_code):
    company_details = AppService.get_company_details(company_reg_code)
    if not company_details:
        return make_response(jsonify({'message': 'Company not found'}), 404)

    return render_template(
        'view-company.html',
        company=company_details['company'],
        individual_shareholders=company_details['individual_shareholders'],
        legal_entity_shareholders=company_details['legal_entity_shareholders']
    )


@company_bp.route('/create-company', methods=['GET'])
def create_company_form():
    return render_template('create-company.html')


@company_bp.route('/create-company', methods=['POST'])
def create_company():
    try:
        data = request.get_json()
        new_company = AppService.create_company(data)
        return make_response(
            jsonify({'message': 'Company and shareholders created', 'company_reg_num': new_company.registration_code}),
            201)
    except ValueError as e:
        return make_response(jsonify({'message': f'Error creating company: {e}'}), 400)
    except Exception as e:
        return make_response(jsonify({'message': f'Unexpected error: {e}'}), 500)


@company_bp.route('/search', methods=['GET'])
def search_companies():
    try:
        name = request.args.get('name')
        registration_code = request.args.get('registration_code')
        shareholder_name = request.args.get('shareholder_name')
        shareholder_code = request.args.get('shareholder_code')
        shareholder_type = request.args.get('shareholder_type')

        companies = AppService.search_companies(name, registration_code, shareholder_name, shareholder_code,
                                                shareholder_type)

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
