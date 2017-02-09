# -*- coding: utf-8 -*-

"""
Main class of the Rest API. Here we define endpoints with their functions. Also we define some configuration
for Flask and manage error codes.

"""

from __future__ import print_function

import logging
from datetime import timedelta
from functools import wraps
from json import dumps, loads
from flask import Flask, request, make_response, Response, abort, redirect, url_for, session, flash, jsonify, \
    request_finished
from flask_httpauth import HTTPBasicAuth
from sqlalchemy.orm import class_mapper
from packUtils.utilities import Utilities

from packControllers import post_orm, ar_post_orm, sr_post_orm

__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2016, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"


# Configuration
ACTUAL_API = '0.1'
AVAILABLE_API = '0.1', '0.2', '0.3'
SECRET_KEY = '\xc2O\xd1\xbb\xd6\xb2\xc2pxRS\x12l\xee8X\xcb\xc3(\xeer\xc5\x08s'
AR_DATABASE = 'Database'
SR_DATABASE = 'Database'
USER = None
MAX_LENGHT = 8 * 1024 * 1024  # in bytes

# Create application and load config.
app = Flask(__name__)
app.config.from_object(__name__)
auth = HTTPBasicAuth()


def limit_content_length(max_length):
    """
    This is a decorator method that checks if the user is sending too long data. The idea is to have some control
    over user's POST data to avoid server overload.

    If user sends data that is too long this method makes an error code 413

    :param max_length: The maximum length of the requested data in bytes
    :return: decorator if all is ok or an error code 413 if data is too long
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cl = request.content_length
            if cl is not None and cl > max_length:
                abort(413)
            return f(*args, **kwargs)

        return wrapper
    return decorator

###################################################################################################
###################################################################################################
######                              SIGNALS
###################################################################################################
###################################################################################################


@app.before_request
def before_request():
    # Connection
    global AR_DATABASE
    AR_DATABASE = ar_post_orm.ARPostORM()
    global SR_DATABASE
    SR_DATABASE = sr_post_orm.SRPostORM()
    # Make sessions permament with some time
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=30)  # minutes=30 days=232323 years=2312321 and so on.
    session.modified = True  # To force seesion expiration


@app.teardown_request
def teardown_request(exception):
    global AR_DATABASE
    if AR_DATABASE is not None:
        # Close database active session
        AR_DATABASE.close()
    global SR_DATABASE
    if SR_DATABASE is not None:
        # Close database active session
        SR_DATABASE.close()


# TODO uncoment this when you finish to make all changes
"""

@request_finished.connect_via(app)
def when_request_finished(sender, response, **extra):
    # We want to check if it is a registered user POST call.
    if request.url_rule.rule != '/api/<version>/login' \
            and request.method == 'POST' and session.get('token', False):
        # There is a registered user sending DATA
        # ALL is ok we register the event
        user_id = Utilities.check_session(app, AR_DATABASE).id
        route = request.url_rule and request.url_rule.endpoint or "Bad route or method"
        ip = request.remote_addr or "Can read user Ip Address"
        agent = request.user_agent.string or "User is not sending its agent"
        data = "User entered an JSON with length of: %s" % request.content_length or "No data found"
        status_code = response.status_code or "No status code. Check estrange behavior"

        res = AR_DATABASE.add_historical(user_id, route, ip, agent, data, status_code)
        if not res:
            logging.error("Historical data is not storing well into DB. The sent data is the following:"
                          "\n User id: %s"
                          "\n Route: %s"
                          "\n Ip Address: %s"
                          "\n User Agent: %s"
                          "\n Data: %s"
                          "\n Status code?: %s", user_id, route, ip, agent, data, status_code)

"""


###################################################################################################
###################################################################################################
######                              AUTH METHODS
###################################################################################################
###################################################################################################


@auth.verify_password
def verify_password(username_or_token, password):
    """
    This decorator is used by Flask-HTTPauth to stablish the user's password verification process.

    The method is defined to validate user when it sends either its username/password or token.

    :param username_or_token: The username or validation token
    :param password: The user password

    :return: True if the user credentials are ok
            False if the user credentials are ko

    """

    if session and session.get('token', False):
        # Validating user using the encrypted cookie.
        user = AR_DATABASE.verify_auth_token(session['token'], app)
    else:
        # Validating user using the auth Token.
        user = AR_DATABASE.verify_auth_token(username_or_token, app)
    if not user:
        # Validating user with username/password.
        user = AR_DATABASE.verify_user_login(username_or_token, password, app)
        if not user:
            Utilities.write_log_error(app, "login: User entered an invalid username or password. 401")
            return False
    # Put the user id in a global stage
    global USER
    USER = user
    # Writing the log
    Utilities.write_log_info(app, ("login: User login successfully with username or token: %s" % username_or_token))
    return True


@app.route('/api/<version>/login', methods=['GET'])
@auth.login_required
@limit_content_length(MAX_LENGHT)
def login(version=app.config['ACTUAL_API']):
    """
    Gives the ability to login into API. It returns an encrypted cookie with the token information and a JSON containing
    the string of the token to use in the validation process.

    :param version: Api version
    :return: A token with user ID information in two formats: 1) in a cookie encrypted; 2) in a JSON decoded.
    """
    if Utilities.check_version(app, version):
        # We retieve the actual loggin user information
        if USER:
            token = AR_DATABASE.get_auth_token(USER, app, expiration=600)
            session['token'] = token
            return jsonify({'token': token.decode('ascii')})


@app.route('/api/<version>/logout', methods=['GET'])
@auth.login_required
def logout(version=app.config['ACTUAL_API']):
    """
    Logout from the system and removes session mark

    :param version: APi version
    :return:
    """
    if Utilities.check_version(app, version):
        global USER
        if USER:
            session.pop('token', None)
            USER = None
            Utilities.write_log_info(app, ("logout: User logout successfully"))
            flash('You were logged out')
            return redirect(url_for('api', version=app.config['ACTUAL_API']))
    else:
        Utilities.write_log_error(app, "logout: User entered an invalid api version, 404")
        return "You have entered an invalid api version", 404



###################################################################################################
###################################################################################################
######                              GET FUNCTIONS
###################################################################################################
###################################################################################################


@app.route('/')
def index():
    """
    Redirect to the latest  API version

    :return: Redirect to the latest api version
    """
    logging.info("Redirection to last api version.....")
    return redirect(url_for('api', version=app.config['ACTUAL_API']))


@app.route('/api')
def api_redirect():
    """
    Redirect to the latest API version

    :return: Redirection to the current api version
    """
    logging.info("Redirection to last api version.....")
    return redirect(url_for('api', version=app.config['ACTUAL_API']))


@app.route('/api/<version>')
def api(version=app.config['ACTUAL_API']):
    """
    This is our main page.

    :param version: Api version
    :return:
    """
    if Utilities.check_version(app, version):
        return """<h1>Welcome to City4Age Rest API</h1>

        Here you have a list of available commands to use:

        This API is designed to be used with curl and JSON request.

        <ul>
            <li><b>add_action</b>: Adds new ExecutedAction into database.</li>
            <li><b>add_activity</b>: Adds new Activity into database.</li>
            <li><b>login</b>: Login into API.</li>
            <li><b>logout</b>: Disconnect current user from the API.</li>
            <li><b>search</b>: Search some datasets.</li>
        </ul>

        """
    else:
        return "You have entered an invalid api version", 404


@app.route("/get_my_info", methods=["GET"])
def get_my_ip():
    return jsonify({'ip': request.remote_addr,
                    'platform': request.user_agent.string,
                    }), 200

###################################################################################################
###################################################################################################
######                              POST functions
###################################################################################################
###################################################################################################


@app.route('/api/<version>/search', methods=['POST'])
@auth.login_required
@limit_content_length(MAX_LENGHT)
def search(version=app.config['ACTUAL_API']):
    """
    Return data based on specified search filters:

    Example of JSON search call:

    {
        'table': 'table_name',
        'criteria': {
            "col1": "value",
            "col2": "value"
        },
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
    if Utilities.check_connection(app, version):
        data = _convert_to_dict(request.json)[0]
        if Utilities.check_search(AR_DATABASE, data) and USER:
            # data Entered by the user is OK
            limit = data.get('limit', 10) if data and data.get('limit', 10) >= 0 else 10
            offset = data.get('offset', 0) if data and data.get('offset', 0) >= 0 else 0
            order_by = data.get('order_by', 'asc') if data and data.get('order_by', 'asc') in ['asc', 'desc'] else 'asc'
            # Obtain table class using the name of the desired table
            table_class = AR_DATABASE.get_table_object_by_name(data['table'])
            # Query database and select needed elements
            try:
                res = AR_DATABASE.query(table_class, data['criteria'], limit=limit, offset=offset, order_by=order_by)
                serialized_labels = [serialize(label) for label in res]
                if len(serialized_labels) == 0:
                    Utilities.write_log_warning(app, ("search: the username: %s performs a valid search "
                                                      "with no results" % USER.username))
                    res = Response("No data found with this filters.\n")
                else:
                    Utilities.write_log_info(app, ("search: the username: %s performs a valid search" %
                                                   USER.username))
                    res = Response(dumps(serialized_labels, default=date_handler), mimetype='application/json')
            except AttributeError:
                abort(500)
        else:
            # Some user data is not well
            Utilities.write_log_error(app, ("search: the username: %s performs an INVALID search. 413" %
                                      USER.username))
            res = Response(
                "You have entered incorrect JSON format Data, check if your JSON is OK. Here there are current database"
                "tables, check if you type one of the following tables: %s" % AR_DATABASE.get_tables()
            ), 413
    return res


@app.route('/api/<version>/add_action', methods=['POST'])
@auth.login_required
@limit_content_length(MAX_LENGHT)
def add_action(version=app.config['ACTUAL_API']):
    """
    Add a new action in DB

    An example of add action is described by POLIMI in the following code:

    {
        "action": "eu:c4a:usermotility:enter_bus",
        "location": "it:puglia:lecce:bus:39",
        "payload": {
            "user": "eu:c4a:pilot:madrid:user:12346",
            "position": "urn:ogc:def:crs:EPSG:6.6:4326"
        },
        "timestamp": "2014-05-20 07:08:41.22222",
        "rating": 0.1,
        "extra": {
            "pilot": "lecce"
        },
        "secret": "jwt_token"
    }

    :param version: Api version
    :return:
    """

    if Utilities.check_connection(app, version):
        # We created a list of Python dict.
        data = _convert_to_dict(request.json)
        if data and Utilities.check_add_action_data(data) and USER:
            # User and data are OK. save data into DB
            res = AR_DATABASE.add_action(data)
            if res:
                Utilities.write_log_info(app, ("add_action: the username: %s adds new action into database" %
                                         USER.username))
                return Response('Data stored in database OK\n'), 200
            else:
                Utilities.write_log_error(app, ("add_action: the username: %s failed to store data into database. 500" %
                                          USER.username))
                return "There is an error in DB", 500
        else:
            abort(500)


@app.route('/api/<version>/add_activity', methods=['POST'])
@limit_content_length(MAX_LENGHT)
def add_activity(version=app.config['ACTUAL_API']):
    """
    Adds a new activity into the system


    An example in JSON could be:

    [{
        "activity_name": "kitchenActivity",
        "activity_start_date": "2014-05-20 06:08:41.22222",
        "activity_end_date": "2014-05-20 07:08:41.22222",
        "since": "2014-05-20 01:08:41.22222",
        "house_number": 0,
        "location": {
            "name": "it:puglia:lecce:bus:39",
            "indoor": false
        },
        "pilot": "lecce"
    }, {
        "activity_name": "doBreakFast",
        "activity_start_date": "2015-05-20 06:18:41.22222",
        "activity_end_date": "2015-05-20 07:08:41.22222",
        "since": "2011-05-20 01:08:41.22222",
        "house_number": 2,
        "location": {
            "name": "it:puglia:madrid:house:2",
            "indoor": true
        },
        "pilot": "madrid"
    }]

    :param version: Api version
    :return:
    """
    if Utilities.check_connection(app, version):
        data = _convert_to_dict(request.json)
        if data and Utilities.check_add_activity_data(data) and USER:
            # User and data are OK. save data into DB
            res = AR_DATABASE.add_activity(data)
            if res:
                Utilities.write_log_info(app, ("add_activity: the username: %s adds new action into database" %
                                         USER.username))
                return Response('Data stored in database OK\n'), 200
            else:
                Utilities.write_log_error(app, ("add_activity: the username: %s failed to store "
                                                "data into database. 500" % USER.username))
                return Response("There is an error in DB"), 500
        else:
            abort(500)


@app.route('/api/<version>/add_new_user', methods=['POST'])
@limit_content_length(MAX_LENGHT)
def add_new_user(version=app.config['ACTUAL_API']):
    """
    Adds a new system user into the system. The idea is to add a user with a stakeholder.

    An example in JSON could be:

    {
        "username": "rubennS",
        "password": "ruben",
        "type": "admin"
    }


    :param version: Api version
    :return:
    """
    """
    if Utilities.check_connection(app, version):
        data = _convert_to_dict(request.json)
        # Verifying the user
        user_data = Utilities.check_session(app, DATABASE)
        # Validate new user data
        if data and Utilities.check_add_new_user(data) and user_data.stake_holder_name == "admin":
            # Data entered is ok
            res = DATABASE.add_new_user_in_system(data)
            if res and isinstance(res, list):
                # The user entered a bad state holder. Return something
                Utilities.write_log_warning(app, ("add_new_user: the username: %s entered an invalid stakeholder. 412" %
                                            user_data.username))
                msg = "Your request is not 100% finished because you have entered an invalid stakeholder, please, " \
                      "review your JSON request and set 'type' value to one of the following " \
                      "list to decide what is the best choice for you: \n \n %s" % res
                return Response(msg, 412)
            if res and res is True:
                # Data entered ok
                Utilities.write_log_info(app, ("add_new_user: the username: %s inserts new user into database" %
                                         user_data.username))
                return Response('Data stored in database OK\n'), 200
        else:
            abort(500)
    """
    return Response('Not available\n'), 200


@app.route('/api/<version>/clear_user', methods=['POST'])
@limit_content_length(MAX_LENGHT)
def clear_user(version=app.config['ACTUAL_API']):
    """
    Clear all data related to a list of defined users. This is only can be performed by an administration
    level role. The administrator needs to define the username and its role.

    An example in JSON could be:

    {
        "id": "rubennS",
        "type": "admin"              # Safeguard delete
    }

    :param version: Api version
    :return: A message containing the res of the operation
    """

    if Utilities.check_connection(app, version):
        data = _convert_to_dict(request.json)
        # TODO call to user in role to know the CD_ROLE OF THIS USER

        """
        if data and Utilities.check_clear_user(data) and USER.stake_holder_name == "admin":
            # Data entered is ok
            res = AR_DATABASE.clear_user_data_in_system(data)
            if res:
                Utilities.write_log_info(app, ("clean_user: the username: %s cleans user data" % user_data.username))
                return Response('User data deleted\n'), 200
            else:
                return Response("There isn't data from this entered user", 412)
        else:
            abort(500)
        """


@app.route('/api/<version>/add_measure', methods=['POST'])
@auth.login_required
@limit_content_length(MAX_LENGHT)
def add_measure(version=app.config['ACTUAL_API']):
    """
    Adds a new measure into the system. This endpoint is sensible to different combinations of GEF/GES


    An example in JSON could be:

    {
         "gef": "motility",
         "ges": "still_moving",
         "payload": {
             "user": "eu:c4a:pilot:lecce:user:12345",
             "date": "2016-05-19"
             "tm_secs": "9000"
         },
         "timestamp": "2016-05-20 00:08:41.013329",
         "extra": {
             "pilot": "lecce"
         }
    }


    :param version: Api version
    :return:

    """
    # TODO this method must be developed with measure information from Vladimir
    if Utilities.check_connection(app, version):
        data = _convert_to_dict(request.json)



        """
        if data and Utilities.check_clear_user(data) and user_data.stake_holder_name == "admin":
            res = AR_DATABASE.add_measure(data)
            if res:
                # Utilities.write_log_info(app, ("add_action: the username: %s adds new action into database" %
                #                          user_data.username))
                return Response('Data stored in database OK\n'), 200
            else:
                # Utilities.write_log_error(app, ("add_action: the username: %s failed to store data into database. 500" %
                #                            user_data.username))
                return "There is an error in DB", 500
        else:
            abort(500)

         """

###################################################################################################
###################################################################################################
######                              Error handlers
###################################################################################################
###################################################################################################


@app.errorhandler(400)
def not_found(error):
    error_msg = "An error 400 is happened with the following error msg: %s" % error
    logging.error(error_msg)
    resp = make_response("Your content type or data is not in JSON format or need some arguments\n", 400)
    return resp


@app.errorhandler(500)
def data_sent_error(error):
    error_msg = "An error 500 is happened with the following error msg: %s" % error
    logging.error(error_msg)
    resp = make_response("Data entered is invalid, please check your JSON\n", 500)
    return resp


@app.errorhandler(413)
def data_sent_too_long(error):
    error_msg = "An error 413 is happened with the following error msg: %s" % error
    logging.error(error_msg)
    msg = "Data entered is too long, please send data with max length of %d bytes \n" % MAX_LENGHT
    resp = make_response(msg, 413)
    return resp


###################################################################################################
###################################################################################################
######                              Extra functions
###################################################################################################
###################################################################################################

# JSON RELATED
# TODO move this class to intermediate level to filter user password.
def serialize(model):
    """Transforms a model into a dictionary which can be dumped to JSON."""
    # first we get the names of all the columns on your model
    columns = [c.key for c in class_mapper(model.__class__).columns if
               c.key is not 'password']  # Avoids to return password
    # then we return their values in a dict
    return dict((c, getattr(model, c)) for c in columns)


def date_handler(obj):
    """ A simple method to handle and encode Python datetimes to JSON"""
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        raise TypeError


# CONVERSIONS RELATED
def _convert_to_dict(p_requested_data):
    """
    This method checks if current data is in JSON list format or it needs to be convert to one

    :param p_requested_data: A list containing Json Strings datasets or a List of JSON dicts
    :return: A Python dict list, containing requiring data or an error code in some rare cases
    """
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


curl -X POST -k -b cookie.txt -d @json_data.txt -w @curl-format.txt http://0.0.0.0:5000/api/0.1/add_action --header "Content-Type:application/json"


curl -X POST -d '{"name1":"Rodolfo","name2":"Pakorro"}' http://127.0.0.1:5000/add_action --header "Content-Type:application/json"

curl -X POST -k -c cookie.txt -d '{"username":"admin","password":"admin"}' https://10.48.1.49/api/0.1/login --header "Content-Type:application/json"

-c cookie.txt --> Save the actual cookie
-b cookie.txt --> Loads actual cookie

Sample curl to store new actions

curl -X POST -b cookie.txt -k -d @json_data.txt http://0.0.0.0:5000/api/0.1/add_action --header "Content-Type:application/json"



todo we need to add support to role-based system user actions. Some actions can only be performed by certain roles.

"""
