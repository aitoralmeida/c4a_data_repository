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
SECRET_KEY = '\xc2O\xd1\xbb\xd6\xb2\xc2pxRS\x12l\xee8X\xcb\xc3(\xeer\xc5\x08s'
DATABASE = 'Database'
USERNAME = 'admin'
PASSWORD = 'admin'

# Create application and load config.
app = Flask(__name__)
app.config.from_object(__name__)


#todo rember that we need to change the session loggin cookie name

@app.before_request
def before_request():
    global DATABASE
    DATABASE = post_orm.PostgORM()
    # Make sessions permament with some time
    #session.permanent = True
    #app.permanent_session_lifetime = timedelta(minutes=5) # days=232323 years=2312321 blablabla

@app.teardown_request
def teardown_request(exception):
    global DATABASE
    if DATABASE is not None:
        # Close database active session
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

        This API is designed to be used with curl and JSON request.

        <ul>
            <li><b>add</b>: Adds new element into databse.</li>
            <li><b>login</b>: Login into API.</li>
            <li><b>logout</b>: Disconnect current user from the API.</li>
            <li><b>search</b>: Search some datasets.</li>
        </ul

        """
    else:
        return "You have entered an invalid api version", 404


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
                # Loggin OK!
                res = DATABASE.verify_user_login(data)
                if res:
                    session['logged_in'] = True
                    flash('You were logged in')
                    return redirect(url_for('api', version=app.config['ACTUAL_API']))
                else:
                    abort(401)
            else:
                abort(500)
        else:
            abort(400)
    else:
        return "You have entered an invalid api version", 404


@app.route('/api/<version>/logout', methods=['POST'])
def logout(version=app.config['ACTUAL_API']):
    """
    Logout from the system and removes session mark

    :param version: APi version
    :return:
    """
    if _check_version(version):
        session.pop('logged_in', None)
        flash('You were logged out')
        return redirect(url_for('api', version=app.config['ACTUAL_API']))
    else:
        return "You have entered an invalid api version", 404


@app.route('/api/<version>/search', methods=['POST'])
def search(version=app.config['ACTUAL_API']):
    """
    Return data based on specified search filters:

    Example of JSON search call:

    {
        'colum_1': 'value_1',
        'colum_2': 'value_2',
        ###### Optional parameters
        'limit': 2323,
        'offset': 2,
        'order_by': 'desc'
    }

    You only need to define a JSON with needed filters and you can optionally add some data to define limits, orders
    and offsets.

    :param version: Api version
    :return:
    """
    res = None
    if _check_version(version):
        if not session.get('logged_in'):
            abort(401)
        if request.headers['content-type'] == 'application/json':
            data = request.json
            # default query values
            limit = 10
            offset = 0
            order_by = 'asc'
            if data.get('limit', False) and data.get('limit') > 0:
                limit = data.get('limit')
                del data['limit']
            if data.get('offset', False) and data.get('offset') >= 0:
                offset = data.get('offset')
                del data['offset']
            if data.get('order_by', False) and data.get('offset') == 'asc' or data.get('offset') == 'desc':
                order_by = data.get('order_by')
                del data['order_by']
            # Query database and select needed elements
            try:
                res = DATABASE.query(tables.User, data, limit=limit, offset=offset, order_by=order_by)
                serialized_labels = [serialize(label) for label in res]
                if len(serialized_labels) == 0:
                    res = Response("No data found with this filters.\n")
                else:
                    res = Response(dumps(serialized_labels), mimetype='application/json')
            except AttributeError:
                abort(500)
        else:
            abort(400)
    else:
        res = "You have entered an invalid api version", 404

    return res


# todo we need to define add_one and add_multI???
@app.route('/api/<version>/add', methods=['POST'])
def add(version=app.config['ACTUAL_API']):
    """
    Add a new element in DB.


    :param version: Api version
    :return:
    """
    if _check_version(version):
        if not session.get('logged_in'):
            abort(401)
        if request.headers['content-type'] == 'application/json':
            data = request.json
            # validate users data
            if data and _check_data(data):
                print "data is ok"
                # todo add new data based on crieteria. Maybe we need more endpoints
                return Response('Data stored in database OK\n')
            else:
                abort(500)
        else:
            abort(400)
    else:
        return "You have entered an invalid api version", 404

@app.errorhandler(400)
def not_found(error):
    resp = make_response("Your content type or data is not in JSON format or need some arguments\n", 400)
    return resp

@app.errorhandler(500)
def data_sent_error(error):
    resp = make_response("Data entered is invalid, please check your JSON\n", 500)
    return resp


def serialize(model):
    """Transforms a model into a dictionary which can be dumped to JSON."""
    # first we get the names of all the columns on your model
    columns = [c.key for c in class_mapper(model.__class__).columns if c.key is not 'password'] # Avoids to return password
    # then we return their values in a dict
    return dict((c, getattr(model, c)) for c in columns)


def _check_version(p_ver):
    """
    Check if we are using a good api version

    :param p_ver: version
    :return:  True or False if api used is ok.
    """
    api_good_version = False
    if p_ver in app.config['AVAILABLE_API']:
        api_good_version = True
    return api_good_version


def _check_data(p_data):
    """
    Check if data is ok and if the not nullable values are filled.


    :param p_data: data from the user.
    :return: True or False if data is ok.
    """
    res = False
    # todo define what kind of data we need to validate. For the moment we are going to set some basic data
    # Check if JSON has all needed values
    if all(k in p_data for k in ("name", "lastname", "genre", 'age', 'username', 'password')):
        # Check not nullable values:
        if p_data['username'] and p_data['password']:
            # All values ok
            res = True
    return res


"""

curl -X POST -d @filename.txt http://127.0.0.1:5000/add_action --header "Content-Type:application/json"

curl -X POST -d '{"name1":"Rodolfo","name2":"Pakorro"}' http://127.0.0.1:5000/add_action --header "Content-Type:application/json"

"""


