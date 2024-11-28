from flask import Blueprint, request, jsonify, make_response, current_app as app

from ..models import Individual, LegalEntity
from ..services.app_service import AppService

shareholder_bp = Blueprint('shareholder', __name__)


@shareholder_bp.route('/search-shareholder', methods=['GET'])
def search_shareholder():
    """
    Search for shareholders based on the query parameter.

    Query Parameters:
    - query (str): The search term for shareholders.
    - limit (int): The maximum number of results to return (default is 5).
    - offset (int): The number of results to skip (default is 0).

    Returns:
    - JSON response containing the search results and total count.
    """
    try:
        query = request.args.get('query')
        limit = int(request.args.get('limit', 5))
        offset = int(request.args.get('offset', 0))
        result_data = AppService.search_shareholder(query, limit, offset)

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


@shareholder_bp.route('/update-share-amount', methods=['POST'])
def update_share_amount():
    """
    Update the share amounts for shareholders of a company.

    Request Body:
    - company_reg_code (int): The registration code of the company
    - shareholders (list): A list of dictionaries containing shareholder data

    Returns:
    - JSON response indicating the success of the operation.
    """
    try:
        data = request.get_json()
        company_reg_code = data['company_reg_code']
        shareholders = data['shareholders']

        AppService.update_share_amount(company_reg_code, shareholders)

        return jsonify({"message": "Share amounts updated successfully"}), 200
    except Exception as e:
        app.logger.error(f"Error updating share amount: {e}")
        return make_response(jsonify({'message': 'Error updating share amount'}), 500)


@shareholder_bp.route('/add-shareholder', methods=['POST'])
def add_shareholder():
    """
    Add a new shareholder to a company.

    Request Body:
    - data (dict): The data of the shareholder to add, including company reg. code

    Returns:
    - JSON response indicating the success of the operation.
    """
    try:
        data = request.get_json()
        company_reg_code = data['company_reg_code']
        AppService.add_shareholder(data)

        return jsonify({'message': 'Shareholder added successfully'}), 200
    except ValueError as e:
        app.logger.error(f"ValueError adding shareholder: {e}")
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error adding shareholder: {e}")
        return jsonify({'message': 'An unexpected error occurred while adding the shareholder'}), 500
