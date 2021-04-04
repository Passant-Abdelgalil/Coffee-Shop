from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)
 
# uncomment the following line at the first time you run the program,
#       then comment it again
#db_drop_and_create_all()

# ROUTES

@app.route("/drinks")
def get_drinks():
    '''
    a public endpoint, contains only the drink.short() data representation
    returns: json {"success": True, "drinks": drinks}
                where drinks is the list of drinks

    '''
    try:
        drinks = Drink.query.all()

        return jsonify({
            'success': True,
            'drinks': [drink.short() for drink in drinks]
        })
    except Exception as e:
        print(e)
        abort(500)


@app.route("/drinks-detail")
@requires_auth("get:drinks-detail")
# if the user is authorized to get details
def get_drinks_details():
    '''
    requires the 'get:drinks-detail' permission
    contains the drink.long() data representation
    returns: json {"success": True, "drinks": drinks}
                where drinks is the list of drinks
    '''
    try:
        drinks = Drink.query.all()
        return jsonify({
            'success': True,
            'drinks': [drink.long() for drink in drinks]
        })
    except Exception as e:
        abort(500)


@app.route("/drinks", methods=['POST'])
@requires_auth("post:drinks")
# if the user is authorized to add a drink
def create_drink():
    '''
    creates a new row in the drinks table
    requires the 'post:drinks' permission
    contains the drink.long() data representation
    returns: json {"success": True, "drinks": drink}
            where drink an array containing only the newly created drink
    '''
    try:
        # get title and recipe from the request, if they don't meet the requirements
        # a 422 will be raised
        recipe = request.get_json()['recipe']
        title = request.get_json()['title']

        new_drink = Drink(title=title, recipe=json.dumps(recipe))
        new_drink.insert()

        return jsonify({
            "success": True,
            "drinks": [new_drink.long()]
        })

    except Exception:
        abort(422)


@app.route("/drinks/<int:drink_id>", methods=['PATCH'])
@requires_auth("patch:drinks")
# if the user if authorized to update an existing drink
def update_drink(drink_id):
    '''
    update the corresponding row for <id>
    require the 'patch:drinks' permission
    contain the drink.long() data representation
    returns: json {"success": True, "drinks": drink} 
            where drink an array containing only the updated drink
    '''
    try:
        drink_obj = Drink.query.get(drink_id)

        data = request.get_json()
        if 'title' in data:  # if the user wants to update the title
            drink_obj.title = data['title']
        if 'recipe' in data:  # if the user wants to update the recipe
            drink_obj.recipe = json.dumps(data['recipe'])

        drink_obj.update()

        return jsonify({
            "success": True,
            "drinks": [drink_obj.long()]
        })
    except Exception:
        abort(404)


@app.route("/drinks/<int:drink_id>", methods=['DELETE'])
@requires_auth("delete:drinks")
# if the user is authorized to delete an existing drink
def delete_drink(drink_id):
    '''
    delete the corresponding row for <id>
    require the 'delete:drinks' permission
    returns: json {"success": True, "delete": id} 
            where id is the id of the deleted record
    '''
    try:
        drink_obj = Drink.query.get(drink_id)

        drink_obj.delete()
        return jsonify({
            "success": True,
            "delete": drink_id
        })

    except Exception:
        abort(404)


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(AuthError)
def auth_error_func(auth_error):
    return jsonify({
        "success": False,
        "error": auth_error.status_code,
        "message": auth_error.error['code']
    }), auth_error.status_code


@app.errorhandler(HTTPException)
def handle_exception(e):
    '''
    This function is a generic exception handler
    Returns:
        - success value
        - error code
        - error message
        - error description
    '''
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "success": False,
        "error": e.code,
        "message": e.name,
        "description": e.description,

    })
    response.content_type = "application/json"
    return response
