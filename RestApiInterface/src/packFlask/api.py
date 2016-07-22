# -*- coding: utf-8 -*-

"""
Main class of the Rest API. Here we define endpoints with their functions. Also we define some configuration
for Flask and manage error codes.

"""

from json import dumps, loads

from src.packORM import post_orm
from src.packORM import tables
from flask import Flask, request, make_response, Response, abort, redirect, url_for, session, flash
from sqlalchemy.orm import class_mapper
import logging


__author__ = 'Rubén Mulero'
__copyright__ = "foo"   # we need?¿


# Configuration
ACTUAL_API = '0.1'
AVAILABLE_API = '0.1', '0.2', '0.3'
SECRET_KEY = '\xc2O\xd1\xbb\xd6\xb2\xc2pxRS\x12l\xee8X\xcb\xc3(\xeer\xc5\x08s'
DATABASE = 'Database'
MAX_DATASETS = 50

# Create application and load config.
app = Flask(__name__)
app.config.from_object(__name__)



###################################################################################################
###################################################################################################
######                              GET FUNCTIONS
###################################################################################################
###################################################################################################


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
    Redirect to the latest  API version

    :return: Redirect to the latest api version
    """
    return redirect(url_for('api', version=app.config['ACTUAL_API']))


@app.route('/api')
def api_redirect():
    """
    Redirect to the latest API version

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


###################################################################################################
###################################################################################################
######                              POST functions
###################################################################################################
###################################################################################################


@app.route('/api/<version>/login', methods=['POST'])
def login(version=app.config['ACTUAL_API']):
    """
    Gives the ability to login into API

    :param version: Api version
    :return:
    """
    if _check_version(version):
        if request.headers['content-type'] == 'application/json':
            data = _convert_to_dict(request.json)
            if 'username' in data and 'password' in data:
                res = DATABASE.verify_user_login(data)
                if res:
                    # Username and password are OK
                    logging.info("login: User loggin sucesfully with %s username", data['username'])
                    # Saving session cookie.
                    session['username'] = data['username']
                    session['id'] = res
                    # return redirect(url_for('api', version=app.config['ACTUAL_API']))
                    return "You were logged in", 200
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



## todo develop separated searchs!!

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
        # todo define better this part.

        if not session.get('username'):
            abort(401)
        if request.headers['content-type'] == 'application/json':
            data = _convert_to_dict(request.json)
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


@app.route('/api/<version>/add_action', methods=['POST'])
def add(version=app.config['ACTUAL_API']):
    """
    Add a new action in DB

    :param version: Api version
    :return:
    """
    if _check_connection(version):
        # We created a list of Python dics.
        data = _convert_to_dict(request.json)
        # validate users data
        if data and _check_add_action_data(data):
            # User and data are OK. save data into DB
            res = DATABASE.add_action(data)
            if res:
                logging.info("add_action: Stored in database ok")
                return Response('Data stored in database OK\n'), 200
            else:
                logging.error("add_action: Stored in database failed")
                return "There is an error in DB", 500
        else:
            abort(500)


@app.route('/api/<version>/add_activity', methods=['POST'])
def add_activity(version=app.config['ACTUAL_API']):
    """
    Adds a new activity into the system

    :param version: Api version
    :return:
    """
    if _check_connection(version):
        data = _convert_to_dict(request.json)
        username = session['username']
        id = session['id']
        # validate users data
        if data and _check_add_activity_data(data):
            # User and data are OK. save data into DB
            res = DATABASE.add_activity(data)
            if res:
                logging.info("add_activity: Stored in database ok")
                return Response('Data stored in database OK\n'), 200
            else:
                logging.error("add_activity: Stored in database failed")
                return "There is an error in DB", 500
        else:
            abort(500)


@app.route('/api/<version>/add_behavior', methods=['POST'])
def add_behavior(version=app.config['ACTUAL_API']):
    """
    Adds a new behavior into the system

    :param version: Api version
    :return:
    """
    if _check_connection(version):
        data = _convert_to_dict(request.json)
        username = session['username']
        id = session['id']
        # validate users data
        if data and _check_add_behavior_data(data):
            # User and data are OK. save data into DB
            res = DATABASE.add_behavior(data)
            if res:
                logging.info("add_behavior: Stored in database ok")
                return Response('Data stored in database OK\n'), 200
            else:
                logging.error("add_behavior: Stored in database failed")
                return "There is an error in DB", 500
        else:
            abort(500)


@app.route('/api/<version>/add_risk', methods=['POST'])
def add_risk(version=app.config['ACTUAL_API']):
    """
    Adds a new risk into the system

    :param version: Api version
    :return:
    """
    if _check_connection(version):
        data = _convert_to_dict(request.json)
        username = session['username']
        id = session['id']
        # validate users data
        if data and _check_add_risk_data(data):
            # User and data are OK. save data into DB
            res = DATABASE.add_risk(data)
            if res:
                logging.info("add_risk: Stored in database ok")
                return Response('Data stored in database OK\n'), 200
            else:
                logging.error("add_risk: Stored in database failed")
                return "There is an error in DB", 500
        else:
            abort(500)


@app.route('/api/<version>/add_new_user', methods=['POST'])
def add_new_user(version=app.config['ACTUAL_API']):
    """
    Adds a new system user into the system. The idea is to add a user with a stakeholder to create some role based system.

    :param version:
    :return:
    """
    if _check_connection(version):
        data = _convert_to_dict(request.json)
        # Validate new user data
        if data and _check_add_new_user(data):
            # Data entered is ok
            res = DATABASE.add_new_user_in_system(data)
            if res and isinstance(res, list):
                # The user entered a bad state holder. Return something
                msg = "Your request is not 100% finished because you have entered an invalid stakeholder, please, " \
                      "review your JSON request and set 'type' value to one of the following " \
                      "list to decide what is the best choice for you: \n \n %s" % res
                return Response(msg, 412)
            if res and res is True:
                # Data entered ok
                return Response('Data stored in database OK\n'), 200
        else:
            abort(500)


###################################################################################################
###################################################################################################
######                              Error handlers
###################################################################################################
###################################################################################################

@app.errorhandler(400)
def not_found(error):
    resp = make_response("Your content type or data is not in JSON format or need some arguments\n", 400)
    return resp


@app.errorhandler(500)
def data_sent_error(error):
    resp = make_response("Data entered is invalid, please check your JSON\n", 500)
    return resp


@app.errorhandler(413)
def data_sent_too_long(error):
    msg = "Data entered is too long, please send datasets with max length of %d \n" % MAX_DATASETS
    resp = make_response(msg, 413)
    return resp


###################################################################################################
###################################################################################################
######                              Extra functions
###################################################################################################
###################################################################################################


def serialize(model):
    """Transforms a model into a dictionary which can be dumped to JSON."""
    # first we get the names of all the columns on your model
    columns = [c.key for c in class_mapper(model.__class__).columns if c.key is not 'password'] # Avoids to return password
    # then we return their values in a dict
    return dict((c, getattr(model, c)) for c in columns)


def _check_connection(p_ver):
    """
    Make a full check of all needed data


    :param p_ver: Actual version of the API
    :return: True if everithing is OK.
            An error code (abort) if something is bad
    """

    if _check_version(p_ver=p_ver):
        if _check_content_tye():
            if _check_session():
                logging.info("check_connection: User entered data is OK")
                return True
            else:
                logging.error("check_connection: User session cookie is not OK, 401")
                abort(401)
        else:
            logging.error("check_connection: Content-type is not JSON serializable, 400")
            abort(400)
    else:
        logging.error("check_connection, Actual API is WRONG, 404")
        abort(404)


def _check_session():
    """
    Checks if the actual user has a session cookie registered

    :return: True if cookie is ok
            False is there isn't any cookie or cookie is bad.
    """
    res = False
    if session.get('username') and session.get('id'):
        res = True
    return res


def _check_content_tye():
    """
    Checks if actual content_type is OK


    :param p_ver: Actual version of API
    :return: True if everything is ok.
            False if something is wrong
    """
    content_type_ok = False
    # Check if request headers are ok
    if request.headers['content-type'] == 'application/json':
        content_type_ok = True
    return content_type_ok


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


def _check_add_action_data(p_data):
    """
    Check if data is ok and if the not nullable values are filled.


    :param p_data: data from the user.
    :return: True or False if data is ok.
    """
    res = False
    # todo we are going to define add_action data from WP3
    # Check if JSON has all needed values
    for data in p_data:
            if all(k in data for k in ("action", "location", "payload", 'timestamp', 'rating', 'extra', 'secret')):
                if all(l in data['payload'] for l in ("user", "position")):
                    if "pilot" in data['extra']:
                        # todo make sure if we need to ensure that variables ar not null
                        res = True

    return res


def _check_add_risk_data(p_data):
    """
    Check if data is ok and if the not nullable values are filled.

    :param p_data:
    :return: True or False if data i ok
    """
    res = False
    # Check if JSON has all needed values
    for data in p_data:
        if all(k in data for k in ("risk_name", "ratio", "description")):   # todo add the name of behavior or action
            res = True
    return res


def _check_add_behavior_data(p_data):
    """
    Check if data is ok and if the not nullable values are filled.

    :param p_data:
    :return: True or False if data is ok
    """
    res = False
    # Check if JSON has all needed values
    for data in p_data:
        # if all(k in data for k in "behavior_name"):
        if "behavior_name" in data:
            res = True
    return res


def _check_add_activity_data(p_data):
    """
    Check if data is ok and if the not nullable values are filled.

    :param p_data:
    :return: True or False if data is ok
    """
    res = False
    # Check if JSON has all needed values
    for data in p_data:
        # if all(k in data for k in "activity_name"):
        if "activity_name" in data:
            res = True
    return res


def _check_add_new_user(p_data):
    """
    Check if data is ok and if the not nullable values are filled.

    :param p_data:
    :return:  True or False if data is ok
    """
    res = False
    # Check if JSON has all needed values
    for data in p_data:
        # if all(k in data for k in "activity_name"):
        if "username" in data and 'password' in data and 'type' in data:
            res = True
    return res


def _convert_to_dict(p_requested_data):
    """
    This method checks if current data is in JSON list format or it needs to be convert to one

    Furthermore if data is too long, this method returns 413 error code to the user.

    :param p_requested_data: A list containing Json Strings datasets or a List of JSON dicts
    :return: A Python dict list, containing requiring data or an error code if the list is too long
    """
    if len(p_requested_data) > MAX_DATASETS:
        # Entered data is too long
        logging.error("The user sends valid data but is too long")
        abort(413)
    else:
        list_of_dicts = []
        if all(isinstance(n, dict) for n in p_requested_data):
            # We have already a list of dictionaries
            return p_requested_data
        elif isinstance(p_requested_data, dict):
            # This is a simple dict item
            list_of_dicts.append(p_requested_data)
        elif all(isinstance(n, unicode) for n in p_requested_data):
            # This is a list of Json strings
            for dt in p_requested_data:
                list_of_dicts.append(loads(dt))
        else:
            # Something wrong happened
            logging.error("The user sends some estrange dataset list that it is impossible to parse "
                          "into a list of dicts")
            abort(500)

        return list_of_dicts

"""

curl -X POST -d @filename.txt http://127.0.0.1:5000/add_action --header "Content-Type:application/json"

curl -X POST -d '{"name1":"Rodolfo","name2":"Pakorro"}' http://127.0.0.1:5000/add_action --header "Content-Type:application/json"

curl -X POST -k -c cookie.txt -d '{"username":"admin","password":"admin"}' https://10.48.1.49/api/0.1/login --header "Content-Type:application/json"

-c cookie.txt --> Save the actual cookie
-b cookie.txt --> Loads actual cookie

Sample curl to store new actions

curl -X POST -b cookie.txt -k -d @json_data.txt http://0.0.0.0:5000/api/0.1/add_action --header "Content-Type:application/json"




todo we need to add support to role-based system user actions. Some actions can only be performed by certain roles.

"""


