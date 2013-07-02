import json

from flask import jsonify, request, Response
from trellis_api import app, models
from models.entities import sa

@app.route('/')
@app.route('/index')
def index():
    response = jsonify(message="Hello, World!")
    response.status_code = 200

    return response

@app.route('/user', methods=['POST'])
def add_new_user():
    #validate it!


    # Use the ORM's session object to get transactions
    try:
        #request.json only when Content-type: application/json
        #transform to python variable; json.loads is already called in request.json
        # must use ** for kwargs in built-in __init__ to pull them into keywords...
        person = models.entities.Person(**request.json['person'])
        sa.session.add(person)
        sa.session.commit()
    except:
        # on rollback, the same closure of state
        # as that of commit proceeds.
        sa.session.rollback()
        raise

    return jsonify(person.serialize)


@app.route('/user/<username>', methods=['PUT'])
def update_existing_user(username):

    query = models.entities.Account.query.filter_by(username='%s' % username)
    # since update() expects a dict, we don't need **request.json
    rows_updated = query.update(request.json['account'])
    account = query.first_or_404()

    sa.session.commit()

    return jsonify(account.serialize)


@app.route('/user/<username>', methods=['DELETE'])
def delete_existing_user(username):
    account = models.entities.Account.query.filter_by(username='%s' % username).first_or_404()

    rows_deleted = sa.session.delete(account)

    # or
    #rows_deleted = models.entities.Account.query.filter_by(username='%s' % username).delete()

    sa.session.commit()

    return jsonify({"deleted_user": username})


@app.route('/users/', methods=['GET'])
def get_all_users(query=""):
    accounts = models.entities.Account.query.all()
    return jsonify(accounts_list=[i.serialize for i in accounts])
