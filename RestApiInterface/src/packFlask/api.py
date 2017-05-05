# -*- coding: utf-8 -*-

"""
Main class of the Rest API. Here we define endpoints with their functions. Also we define some configuration
for Flask and manage error codes.

"""

from __future__ import print_function

import os
import logging
from datetime import timedelta
from functools import wraps
from json import dumps, loads
from flask import Flask, request, make_response, Response, abort, redirect, url_for, session, flash, jsonify, \
    request_finished
from flask_httpauth import HTTPBasicAuth
from sqlalchemy.orm import class_mapper
from src.packUtils.utilities import Utilities
from itsdangerous import Signer, BadSignature

from src.packControllers import ar_post_orm, sr_post_orm

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

# Signatura verification configuration
# s = Signer(os.urandom(24))


###################################################################################################
###################################################################################################
######                              WRAPPERS
###################################################################################################
###################################################################################################

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
                Utilities.write_log_error(app, "The users sends a too large request data to the server")
                abort(413)
            return f(*args, **kwargs)

        return wrapper
    return decorator


def required_roles(*roles):
    """
    This decorator method checks the current user role into the system and allows the execution of certain endpoints in
     the API.

    :param roles: A list containing required roles
    :return: decorator if all is ok or an
    """

    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_role = AR_DATABASE.get_user_role(USER.id) or None
            if user_role not in roles:
                Utilities.write_log_error(app, "The uses doesn't have permissions to enter to this resource")
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return wrapper


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


@request_finished.connect_via(app)
def when_request_finished(sender, response, **extra):
    # We want to check if it is a registered user POST call.
    if USER:
        # There is a registered user sending DATA so we will register the event
        route = request.url_rule and request.url_rule.endpoint or "Bad route or method"
        ip = request.remote_addr or "Can read user Ip Address"
        agent = request.user_agent.string or "User is not sending its agent"
        data = "User entered an JSON with length of: %s" % request.content_length or "No data found"
        status_code = response.status_code or "No status code. Check estrange behavior"
        # Inserting data into database
        res_ar = AR_DATABASE.add_user_action(USER.id, route, ip, agent, data, status_code)
        res_sr = SR_DATABASE.add_user_action(USER.id, route, ip, agent, data, status_code)
        if not res_ar or not res_sr:
            logging.error("Historical data is not storing well into DB. The sent data is the following:"
                          "\n User id: %s"
                          "\n Route: %s"
                          "\n Ip Address: %s"
                          "\n User Agent: %s"
                          "\n Data: %s"
                          "\n Status code?: %s", USER.id, route, ip, agent, data, status_code)


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

    global USER
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
            # If there are some user session, the system will clear all data to force user to make a successful login.
            session.pop('token', None)
            USER = None
            return False
    # Put the user id in a global stage
    USER = user
    # Writing the log
    Utilities.write_log_info(app, ("login: User login successfully with username or token: %s" % username_or_token))
    return True


@app.route('/api/<version>/login', methods=['GET'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
#@required_roles('administrator', 'geriatrician')
def login(version=app.config['ACTUAL_API']):
    """
    Gives the ability to login into API. It returns an encrypted cookie with the token information and a JSON containing
    the string of the token to use in the validation process.

    :param version: Api version
    :return: A token with user ID information in two formats: 1) in a cookie encrypted; 2) in a JSON decoded.
    """
    if Utilities.check_version(app, version):
        # We relieve the actual logging user information
        if USER:
            token = AR_DATABASE.get_auth_token(USER, app, expiration=600)
            session['token'] = token
            return jsonify({'token': token.decode('ascii')})
    else:
        Utilities.write_log_error(app, "logout: User entered an invalid api version, 404")
        return "You have entered an invalid api version", 404


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
            Utilities.write_log_info(app, "logout: User logout successfully")
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
        return """

        <h1>Welcome to City4Age Rest API</h1>

        Here you have a list of available commands to use:

        This API is designed to be used with curl and JSON request.

        <ul>
            <li><b>login</b>: Obtain an identification user token.</li>
            <li><b>logout</b>: Remove the actual user token from the system.</li>
            <li><b>add_action</b>: Adds new Action into database.</li>
            <li><b>add_activity</b>: Adds new Activity into database.</li>
            <li><b>add_measure</b>: Adds a new Measure into database.</li>
            <li><b>add_eam</b>: Adds information about EAM's in the API related to an activity.</li>
            <li><b>search</b>: Search datasets in database due to some search criteria.</li>
            <li><b>add_care_receiver</b>: Allows to a Pilot add a new user 'care_receiver' in the API.</li>
            <li><b>add_new_user</b>: Adds a new registered user in the system (Administrator only).</li>
            <li><b>clear_user</b>: Delete a user and all its related data from the system (Administrator only).</li>
            <li><b>get_my_info</b>: Returns user information about the actual client.</li>
        </ul>

        """
    else:
        return "You have entered an invalid api version", 404


@app.route("/api/<version>/get_my_info", methods=["GET"])
def get_my_info(version=app.config['ACTUAL_API']):
    """
    A simple endpoint to obtain user agent information if the user request it

    :param version: Api version
    :return:
    """
    return jsonify({'ip': request.remote_addr,
                    'platform': request.user_agent.string,
                    }), 200

###################################################################################################
###################################################################################################
######                              POST functions
###################################################################################################
###################################################################################################


@app.route('/api/<version>/search', methods=['POST'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
@required_roles('administrator', 'geriatrician', 'researcher')
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

    """
    
    res = None
    if Utilities.check_connection(app, version):
        data = _convert_to_dict(request.json)[0]
        
        if data and res and USER:
            # data Entered by the user is OK
            limit = data.get('limit', 10) if data and data.get('limit', 10) >= 0 else 10
            offset = data.get('offset', 0) if data and data.get('offset', 0) >= 0 else 0
            order_by = data.get('order_by', 'asc') if data and data.get('order_by', 'asc') in ['asc', 'desc'] else 'asc'


            # TODO we need to know exactly what kind of tables we need to call


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
    """
    return "Not implemented yet", 501


@app.route('/api/<version>/add_action', methods=['POST'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
@required_roles('administrator', 'geriatrician', 'care_giver')
def add_action(version=app.config['ACTUAL_API']):
    """
    Add a new LEA (Low Elementary Action) into database.
    
    The JSON structure must be in a defined format called Common Data format as:

    {
        "action": "eu:c4a:POI_ENTER",
        "user": " eu:c4a:user:aaaaa",
        "pilot": "ATH",
        "location": "eu:c4a:Shop:Ermou96",
        "position": "37.976908 23.724375",
        "timestamp": "2014-05-20T07:08:41.013+03:00",
        "payload": {
            "instance_id": "124"
        },
        "extra": {
        "data_source_type": ["sensors", "external_dataset"]
        }
    }
    
    :param version: Api version
    :return: Different kind of HTML codes explaining if the action was successful
    """

    if Utilities.check_connection(app, version):
        # We created a list of Python dict.
        data = _convert_to_dict(request.json)
        res, msg = Utilities.check_add_action_data(data)
        if data and res and USER:
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
            return Response(msg), 400


@app.route('/api/<version>/add_activity', methods=['POST'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
@required_roles('administrator', 'geriatrician', 'researcher')
def add_activity(version=app.config['ACTUAL_API']):
    """
    Adds a new activity into the system


    # TODO Instrumental and Basic activities are present HERE!!!! There are two type of Activities
    # Copanion? YES NO boolean

    An example in JSON could be:

    {
        "activity_name": "LeaveHouse",
        "activity_description": "Some description of the activity",          # Optional
        "instrumental": True,                                               # Optional
        "house_number": 0,              # Optional
        "indoor": false,                # Optional
        "location":"eu:c4a:Bus:39",     # Optional
        "pilot": "LCC"                  # Optional
    }

    :param version: Api version
    :return:
    """
    if Utilities.check_connection(app, version):
        data = _convert_to_dict(request.json)
        res, msg = Utilities.check_add_activity_data(AR_DATABASE, data)
        if data and res and USER:
            # User and data are OK. save data into DB
            res = AR_DATABASE.add_activity(data)
            if res:
                Utilities.write_log_info(app, ("add_activity: the username: %s adds new activity into database" %
                                         USER.username))
                return Response('Data stored in database OK\n'), 200
            else:
                Utilities.write_log_error(app, ("add_activity: the username: %s failed to store "
                                                "data into database. 500" % USER.username))
                return Response("There is an error in DB"), 500
        else:
            return Response(msg), 400


@app.route('/api/<version>/add_new_user', methods=['POST'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
@required_roles('administrator')
def add_new_user(version=app.config['ACTUAL_API']):
    """
    Adds a new system user into the system. The idea is give to an user in the system, an system access.

    An example in JSON could be:

    {
        "username": "rubennS",
        "password": "ruben",
        "valid_from": "2014-05-20T07:08:41.013+03:00", **# OPTIONAL
        "valid_to": "2018-05-20T07:08:41.013+03:00", **# OPTIONAL
        "user": "eu:c4a:user:1234567", # OPTIONAL
        "roletype": "administrator",
        "pilot": "ath"
    }
    
    
    There are optional parameters that are used only if the administrator wants to add access credentials to ana ctive
    user in the system.
    

    :param version: Api version
    :return:
    """
    if Utilities.check_connection(app, version):
        data = _convert_to_dict(request.json)
        # check the JSON data
        res, msg = Utilities.check_add_new_user_data(AR_DATABASE, data)
        if data and res and USER:
            # User and entered data are OK. save new user into DB
            res_ar = AR_DATABASE.add_new_user_in_system(data)
            res_sr = SR_DATABASE.add_new_user_in_system(data)
            if res_ar and res_sr:
                Utilities.write_log_info(app, ("add_new_user: the username: %s adds new user into database" %
                                         USER.username))

                return Response('The user(s) are registered successfully in the system: ', jsonify(res_ar), 200)
            else:
                Utilities.write_log_error(app, ("add_new_user: the username: %s failed to store "
                                                "data into database. 500" % USER.username))
                return Response("There is an error in DB"), 500
        else:
            return Response(msg), 400


@app.route('/api/<version>/add_care_receiver', methods=['POST'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
@required_roles('application_developer', 'administrator')
def add_care_receiver(version=app.config['ACTUAL_API']):
    """
    This method allow to the Pilots (roletype: developers) to add new users in the system with the role
    care_receivers
    
    An example in JSON could be:

    {
        "pilot_user_source_id": "xxXXX?????",
        "valid_from": "2014-05-20T07:08:41.013+03:00", ** OPTIONAL
        "valid_to": "2018-05-20T07:08:41.013+03:00", ** OPTIONAL
        "username": "rubennS",
        "password": "ruben"
    }
    
    :param version: 
    :return: A urn with --> eu:c4a:user:{city4AgeId}
    """

    if Utilities.check_connection(app, version):
        data = _convert_to_dict(request.json)
        # Checking if INPUT json is OK
        res, msg = Utilities.check_add_care_receiver_data(AR_DATABASE, data)
        if data and res and USER:
            # User and entered data are OK. save new user into DB
            res_ar = AR_DATABASE.add_new_care_receiver(data, USER.id)
            res_sr = SR_DATABASE.add_new_care_receiver(data, USER.id)
            if res_ar and res_sr:
                Utilities.write_log_info(app, ("add_care_receiver: the username: %s adds new care receiver "
                                               "into database" % USER.username))
                # We only return one value, because both database has the same IDS
                return jsonify(res_ar)

            else:
                Utilities.write_log_error(app, ("add_care_receiver: the username: %s failed to store "
                                                "data into database. 500" % USER.username))
                return Response("There is an error in DB"), 500
        else:
            return Response(msg), 400


@app.route('/api/<version>/clear_user', methods=['POST'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
@required_roles('administrator')
def clear_user(version=app.config['ACTUAL_API']):
    """
    Clear all data related to a list of defined users. This is only can be performed by an administration
    level role. The administrator needs to define the username and its role.

    An example in JSON could be:

    {
        "id": "eu:c4a:pilot:lecce:user:12345",
    }

    :param version: Api version
    :return: A message containing the res of the operation
    """

    # TODO this class will be coded when all database structure has in stable stage

    """
    if Utilities.check_connection(app, version):
        data = _convert_to_dict(request.json)
        if data and Utilities.check_clear_user_data(data) and USER:
            # We are going to check if data has a self-signed certificate
            try:
                id = s.unsign(data[0]['id'])
                # Clearing user data
                Utilities.write_log_warning(app, "clean_user: deleting all user data from the system")
                # TODO call to AR and SR datanase to delete ALL user data from the system

                #ar_res = AR_DATABASE.clear_user_data_in_system(data)
                #sr_res = SR_DATABASE.cls  # More cleaning here


                # @@@@@@@@@@@@@@@@@@@
                res = True
                if res:
                    Utilities.write_log_info(app, ("clean_user: the administrator deletes the user : %s " % data[0]['id']))
                    return Response('User data deleted from system\n'), 200
            except BadSignature:
                # Admin sends an invalid signed signature. We are going to check if user exist and create a signed user
                # to validate its intentions.
                exist = AR_DATABASE.check_user_in_role(data[0]['id'])
                if exist:
                    # User exist in database, we signed its username.
                    id_signed = s.sign(data[0]['id'])
                    Utilities.write_log_info(app, "clean_user: generating a self-signed user to ensure deletion")
                    return jsonify(summary="Send again the deletion useranme using the 'id' value of dis json",
                                   id=id_signed), 200
                else:
                    # User not exist in database
                    return "The entered user do not exist in the system", 418

        else:
            abort(500)

    """
    return "Not implemented yet", 501


@app.route('/api/<version>/add_measure', methods=['POST'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
@required_roles('administrator', 'geriatrician')
def add_measure(version=app.config['ACTUAL_API']):
    """
    Adds a new measure into the system. This endpoint is sensible to different combinations of GEF/GES


    An example in JSON could be:

    {
        "user": "eu:c4a:user:12345",
        "pilot": "SIN",
        "interval_start": "2014-01-20T00:00:00.000+08:00",
        "duration": "DAY",                                  # OPTIONALLY COULD BE INTERVAL_END
        "payload": {
          "WALK_STEPS": { "value": 1728 },
          "SHOP_VISITS": { "value": 3, "data_source_type": ["sensors", "external_dataset"]},
          "PHONECALLS_PLACED_PERC": { "value": 21.23, "data_source_type": ["external_dataset"] }
        },
        "extra": {
          "pilot_specific_field": “some value”
        }
    }

    :param version: Api version
    :return:

    """
    if Utilities.check_connection(app, version):
        # We created a list of Python dict.
        data = _convert_to_dict(request.json)
        res, msg = Utilities.check_add_measure_data(data)
        if data and res and USER:
            # User and data are OK. save data into DB
            res = SR_DATABASE.add_measure(data)
            if res:
                Utilities.write_log_info(app, ("add_measure: the username: %s adds new action into database" %
                                         USER.username))
                return Response('add_measure: data stored in database OK\n'), 200
            else:
                Utilities.write_log_error(app, ("add_measure: the username: %s failed to store data into database. 500" %
                                          USER.username))
                return "There is an error in DB", 500
        else:
            return Response(msg), 400


@app.route('/api/<version>/add_eam', methods=['POST'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
@required_roles('researcher', 'application_developer', 'administrator')
def add_eam(version=app.config['ACTUAL_API']):
    """
    This endpoint allows to pilots insert information about related EAMS from different type of activities.

    It allow to Expert Activity Model, have an input access to discover new activities based on user performed actions.


    An example in JSON could be:

    {
        "activity_name": "AnsweringPhone",
        "locations": ["Kitchen", "Office", "Bedroom"],
        "actions": ["KitchenPIR", "BedroomPIR"],
        "duration": 120,
        "start": [
            ["12:00", "12:05"],
            ["20:00", "20:10"]
        ]
    }


    :param version: Api version
    :return:
    """
    if Utilities.check_connection(app, version):
        # We created a list of Python dict.
        data = _convert_to_dict(request.json)
        res, msg = Utilities.check_add_eam_data(AR_DATABASE, data)
        if data and res and USER:
            # The user data are correct. We proceed to insert it into DB
            res = AR_DATABASE.add_eam(data)
            if res:
                Utilities.write_log_info(app, ("add_eam: the username: %s adds new EAM into database" %
                                         USER.username))
                return Response('add_eam: data stored in database OK\n'), 200
            else:
                Utilities.write_log_error(app, ("add_eam: the username: %s failed to store data into database. 500" %
                                          USER.username))
                return "There is an error in DB", 500
        else:
            return Response(msg), 400


###################################################################################################
###################################################################################################
######                              Error handlers
###################################################################################################
###################################################################################################


@app.errorhandler(500)
def data_sent_error(error):
    error_msg = "An error 500 is happened with the following error msg: %s" % error
    logging.error(error_msg)
    resp = make_response("Data entered is invalid, please check your JSON\n", 500)
    return resp


@app.errorhandler(400)
def data_sent_error(error):
    error_msg = "An error 400 is happened with the following error msg: %s" % error
    logging.error(error_msg)
    resp = make_response("You have sent a bad request. If your request contains a JSON based structure"
                         "check it might be bad formatted.", 400)
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
Different curl examples:


curl -u rubuser:testingpassw -i -X GET http://0.0.0.0:5000/api/0.1/login


curl -X POST -k -b cookie.txt -d @json_data.txt -w @curl-format.txt http://0.0.0.0:5000/api/0.1/add_action --header "Content-Type:application/json"


-c cookie.txt --> Save the actual cookie
-b cookie.txt --> Loads actual cookie
-u username:password --> HTTP auth method login

Sample curl to store new actions
===================================

# Using cookie
curl -X POST -b cookie.txt -k -d @json_data.txt http://0.0.0.0:5000/api/0.1/add_action --header "Content-Type:application/json"
# Using token
curl -u eyJhbGciOiJIUzI1NiIsImV4cCI6MTQ4NjcyMjU5OSwiaWF0IjoxNDg2NzIxOTk5fQ.eyJpZCI6M30.op_1X9YUqFgKqXorO73JT6bw36jm_ttqAbDnJtcaKA8 -X POST -k -d @json_data_sample.txt http://0.0.0.0:5000/api/0.1/add_action --header "Content-Type:application/json"


Sample curl to store new measures
====================================

# Using username and password
curl -u admin:admin -i -X POST  -d @json_add_measure.txt  http://0.0.0.0:5000/api/0.1/add_measure --header "Content-Type:application/json"


Sample curl to store an action
====================================

curl -u admin:admin -i -X POST -d @json_add_action.txt  http://0.0.0.0:5000/api/0.1/add_action --header "Content-Type:application/json"

"""
