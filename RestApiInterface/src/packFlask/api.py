# -*- coding: utf-8 -*-

"""
IN this clase we define REST API actions. We define what url is needed and what actions we need to perform

"""

from json import dumps
from src.packORM import post_orm
from src.packORM import tables
from flask import Flask, request, make_response, Response, abort, redirect, url_for, session, flash
from sqlalchemy.orm import class_mapper


__author__ = 'Rubén Mulero'
__copyright__ = "foo"   # we need?¿


# Configuration
ACTUAL_API = '0.1'
AVAILABLE_API = '0.1', '0.2', '0.3'
SECRET_KEY = 'development key'
DATABASE = 'Database'
USERNAME = 'admin'
PASSWORD = 'admin'

# Create application and load config.
app = Flask(__name__)
app.config.from_object(__name__)


@app.before_request
def before_request():
    global DATABASE
    DATABASE = post_orm.PostgORM()

@app.teardown_request
def teardown_request(exception):
    global DATABASE
    if DATABASE is not None:
        DATABASE.close()

@app.route('/')
def index():
    """
    Redirect to the latest version

    :return: Redirect to the latest api version
    """
    return redirect(url_for('api', version=app.config['ACTUAL_API']))


@app.route('/api')
def api_redirect():
    """
    Redirect to the latest version

    :return: Redirection to the current api version
    """
    return redirect(url_for('api', version=app.config['ACTUAL_API']))


@app.route('/api/<version>')
def api(version=app.config['ACTUAL_API']):
    """
    This is our main page.

    :param version:
    :return:
    """
    if _check_version(version):
        return """<h1>Welcome to City4Age Rest API</h1>

        Here you have a list of available commands to use:

        /s  --> Search datasets (can be modified by limit and offset

        """
    else:
        #todo list available apis
        return "You have entered a invalid api version", 404


@app.route('/api/<version>/login', methods=['POST'])
def login(version=app.config['ACTUAL_API']):
    """
    Gives the hability to login in the API an insert new DATA

    :param version: Api version
    :return:
    """
    if _check_version(version):
        if request.headers['content-type'] == 'application/json':
            data = request.json
            if 'username' in data and 'password' in data:
                # Credentials ok
                res = DATABASE.verify_user_login(data, app, expiration=600)

                """
                    # Redirect
                    return redirect(url_for('api', version=app.config['ACTUAL_API']))
                """
                return res

        else:
            abort(400)
    else:
        return "You have entered a invalid api version", 404


@app.route('/api/<version>/logout', methods=['POST'])
def logout(version=app.config['ACTUAL_API']):
    """
    Logout from the system and removes session mark

    :param version:
    :return:
    """
    if _check_version(version):
        session.pop('logged_in', None)
        flash('You were logged out')
        return redirect(url_for('show_entries'))
    else:
        return "You have entered a invalid api version", 404


@app.route('/api/<version>/search', methods=['GET', 'POST'])
def search(version=app.config['ACTUAL_API']):
    """
    Return a specified search pattern

    :param version: Api version
    :return:
    """
    if _check_version(version):
        if request.method == 'POST':
            # JSON based Search
            if request.headers['content-type'] == 'application/json':
                data = request.json
                # Query database and select needed elements
                res = DATABASE.query(tables.User, data)
                serialized_labels = [serialize(label) for label in res]
                return Response(dumps(serialized_labels), mimetype='application/json')
            else:
                abort(400)
        else:
            # Args based search
            # arguments, i.e ?lastname=some-value)
            # lastname = request.args.get('lastname')
            # todo if we have args we need to see if are or not correct
            res = DATABASE.query(tables.User, request.args)
            serialized_labels = [serialize(label) for label in res]
            return Response(dumps(serialized_labels), mimetype='application/json')

    else:
        return "You have entered a invalid api version", 404


@app.route('/api/<version>/add', methods=['POST'])
def add(version=app.config['ACTUAL_API']):
    if _check_version(version):
        if request.headers['content-type'] == 'application/json':
            # Check if token is ok
            data = request.json
            if data.get('token', False):
                user_id = DATABASE.verify_auth_token(data['token'], app)
                if user_id:
                    pass
                else:
                    return "Token Expired or incorrect"
            else:
                abort(500)
        else:
            abort(400)
    else:
        return "You have entered a invalid api version", 404


# TODO only for example

@app.route('/add_action', methods=['GET', 'POST'])
def add_action():
    if request.method == 'POST':
        # Ensure that we are sending Json format data
        if request.headers['content-type'] == 'application/json':
            data = request.json  # Request data in JSON formar if is bad flask makes a 400 response
            if data and 'location' in data: # todo we can send empty data? and data.get('location') is not none.....
                new_location = tables.Location(location=data.get('location', None))  # Creating new location
                orm = post_orm.PostgORM()
                # Need to control this part
                orm.insert_one(new_location)
                # Commit and close
                orm.commit()
                resp = make_response("Data stored in DB OK \n")
                return resp
            else:
                # Data is incorrect
                abort(500)
        else:
            # User submitted an unsupported Content-Type
            abort(400)
    else:
        orm = post_orm.PostgORM()
        # Return one user: This is an example test
        res = orm.query(tables.User, None)
        # todo we need to decide if we want to request all datasets or only one.
        serialized_labels = [serialize(label) for label in res]
        #res_json = dumps(serialized_labels)

        # Only one dataset
        #return jsonify(**serialized_labels[0])

        # multiple datasets(not recommended)
        return Response(dumps(serialized_labels), mimetype='application/json')


@app.errorhandler(400)
def not_found(error):
    resp = make_response("Your content type or data is not in JSON format or need some arguments\n", 400)
    return resp

@app.errorhandler(500)
def data_sent_error(error):
    resp = make_response("Data entered is invalid, please check your JSON headers\n", 500)
    return resp


def serialize(model):
    """Transforms a model into a dictionary which can be dumped to JSON."""
    # first we get the names of all the columns on your model
    columns = [c.key for c in class_mapper(model.__class__).columns]
    # then we return their values in a dict
    return dict((c, getattr(model, c)) for c in columns)


def _check_version(p_ver):
    """
    Check if we are using a good api version

    :param p_ver: version
    :return:  True or False
    """
    api_good_version = False
    if p_ver in app.config['AVAILABLE_API']:
        api_good_version = True
    return api_good_version


"""

curl -X POST -d @filename.txt http://127.0.0.1:5000/add_action --header "Content-Type:application/json"

curl -X POST -d '{"name1":"Rodolfo","name2":"Pakorro"}' http://127.0.0.1:5000/add_action --header "Content-Type:application/json"

"""


