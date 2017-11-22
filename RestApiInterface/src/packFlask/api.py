# -*- coding: utf-8 -*-

"""
Main class of the Rest API. Here we define endpoints with their functions. Also we define some configuration
for Flask and manage error codes.

"""

from __future__ import print_function
import logging
import inspect
from datetime import timedelta
from functools import wraps
from json import dumps, loads
from flask import Flask, request, make_response, Response, abort, redirect, url_for, session, flash, jsonify, \
    request_finished, render_template
from flask_httpauth import HTTPBasicAuth
from sqlalchemy.orm import class_mapper
from src.packUtils.utilities import Utilities
from itsdangerous import Signer, BadSignature
from src.packControllers import ar_post_orm, sr_post_orm

__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2017, City4Age project"
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
AR_DATABASE = None
SR_DATABASE = None
USER = None
MAX_LENGHT = 1398101  # in bytes        ~~ 500 LEAS OR up to 16MB? check if it whort it

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

    :param string max_length: The maximum length of the requested data in bytes

    :return: decorator if all is ok or an error code 413 if data is too long
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cl = request.content_length
            if cl is not None and cl > max_length:
                logging.error("The users sends a too large request data to the server")
                abort(413)
            return f(*args, **kwargs)

        return wrapper

    return decorator


def required_roles(*roles):
    """
    This decorator method checks the current user role into the system and allows the execution of certain endpoints in
     the API.

    :param list roles: A list containing required roles

    :return: decorator if all is ok or an
    """

    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_role = AR_DATABASE.get_user_role(USER.id) or None
            if user_role not in roles:
                logging.error("The uses doesn't have permissions to enter to this resource")
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
    if not AR_DATABASE:
        AR_DATABASE = ar_post_orm.ARPostORM()
    global SR_DATABASE
    if not SR_DATABASE:
        SR_DATABASE = sr_post_orm.SRPostORM()
    # Make sessions permanent with some time
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=30)  # minutes=30 days=232323 years=2312321 and so on.
    session.modified = True  # To force session expiration


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


@app.after_request
def after_request(response):
    """
    This signal is used to write information in the INFO log

    :param response: The needed information

    :return: The response instance
    """
    # If the action is succesfull we write into INFO log file
    route = request.url_rule and request.url_rule.endpoint or "No route provided"
    method = request.method or "No method provided"
    ip = request.remote_addr or "No IP provided"
    agent = request.user_agent.string or "No user_agent provided"
    status = response.status or "No Status provided"
    data = response.data or "No data provided"
    # Writing into log file
    app.logger.info("%s - %s - %s- %s - %s - %s" % (ip, agent, method, route, status, data))
    return response


@request_finished.connect_via(app)
def when_request_finished(sender, response, **extra):
    """
    When all the process is finished, we write into database the user performed command with its response and
    relevant data

    :param sender: The sender data
    :param response: The server response data
    :param extra: Extra data from the server
    :return: None
    """

    # We want to check if it is a registered user POST call.
    if USER:
        # There is a registered user sending DATA so we will register the event
        route = request.url_rule and request.url_rule.endpoint or "Bad route or method"
        ip = request.remote_addr or "Can read user Ip Address"
        agent = request.user_agent.string or "User is not sending its agent"

        # TODO change this part to detect if a user SENDS OR NO A JSON TO THE SERVER

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

    :param basestring username_or_token: The username or validation token
    :param basestring password: The user password

    :return: True if the user credentials are ok
            False if the user credentials are ko
    :rtype: bool
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
            # If there are some user session, the system will clear all data to force user to make a successful login.
            session.pop('token', None)
            USER = None
            return False
    # Put the user id in a global stage
    USER = user
    return True


# TODO this method needs to be used to log user in the system when we decide to disable the login process

@app.route('/api/<version>/login', methods=['GET'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
# @required_roles('administrator', 'geriatrician')
def login(version=app.config['ACTUAL_API']):
    """
    Gives the ability to login into API. It returns an encrypted cookie with the token information and a JSON containing
    the string of the token to use in the validation process.

    :param basestring version: Api version

    :return: A token with user ID information in two formats: 1) in a cookie encrypted; 2) in a JSON decoded.
    """
    if Utilities.check_version(app, version):
        # We relieve the actual logging user information
        if USER:
            token = AR_DATABASE.get_auth_token(USER, app, expiration=600)
            session['token'] = token
            logging.info("login: User logged successfully")
            return jsonify({'token': token.decode('ascii')})
    else:
        logging.error("login: User entered an invalid api version, 404")
        return "You have entered an invalid api version", 404


@app.route('/api/<version>/logout', methods=['GET'])
@auth.login_required
def logout(version=app.config['ACTUAL_API']):
    """
    Logout from the system and removes session mark

    :param basestring version: APi version

    :return: Redirection of the API
    """
    if Utilities.check_version(app, version):
        global USER
        if USER:
            session.pop('token', None)
            USER = None
            logging.info("logout: User logout successfully")
            flash('You were logged out')
            return redirect(url_for('api', version=app.config['ACTUAL_API']))
    else:
        logging.error("logout: User entered an invalid api version, 404")
        return "You have entered an invalid api version", 404


###################################################################################################
###################################################################################################
######                              Error handlers
###################################################################################################
###################################################################################################

@app.errorhandler(500)
def data_sent_error(error):
    resp = make_response("Data entered is invalid, please check your JSON\n", 500)
    return resp


@app.errorhandler(400)
def data_sent_error(error):
    resp = make_response("You have sent a bad request. If your request contains a JSON based structure"
                         "check it might be bad formatted.", 400)
    return resp


@app.errorhandler(413)
def data_sent_too_long(error):
    msg = "Data entered is too long, please send data with max length of %d bytes \n" % MAX_LENGHT
    resp = make_response(msg, 413)
    return resp


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

    :param basestring version: Api version

    :return: Render with the index page of the API
    """
    if Utilities.check_version(app, version):
        # Loading main page of the APi
        return render_template('index.html')
    else:
        return "You have entered an invalid api version", 404


@app.route("/api/<version>/get_my_info", methods=["GET"])
@auth.login_required
def get_my_info(version=app.config['ACTUAL_API']):
    """
    This endpoint returns user information given its login credentials

    :param basestring version: Api version

    :return: The Pilot of the user and its role in the system
    """
    if USER:
        # Obtaining user information
        pilot = AR_DATABASE.get_user_pilot(USER.id)
        role = AR_DATABASE.get_user_role(USER.id)

        # Writing the log and returning data
        logging.info("get_my_info: the username: %s get it's personal info" % USER.username)

        return jsonify({'ip': request.remote_addr,
                        'platform': request.user_agent.string,
                        'pilot': pilot or "n/a",
                        'role': role or "n/a"
                        }), 200
    else:
        # There isn't' any global user, estrange error
        logging.error("get_my_info: Something estrange happened with the USER global parameter.")
        return Response("Some estrange error happened in the server, contact with administrator", 500)


###################################################################################################
###################################################################################################
######                              POST functions
###################################################################################################
###################################################################################################

@app.route('/api/<version>/search', methods=['POST'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
@required_roles('administrator', 'system', 'Pilot source system')
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

    :param basestring version: Api version

    :return: Response of the request
    """

    # TODO this endpoint will be different if the user is admin or pilot --> Using roles
    ########################################################3

    if Utilities.check_connection(app, version):
        # We created a list of Python dict.
        data = _convert_to_dict(request.json)
        if len(data) == 1:
            msg = Utilities.check_search_data(AR_DATABASE, SR_DATABASE, data)
            if data and not msg and USER:
                # User and data are OK. save data into DB
                # Finding the desired table in the proper schema
                is_ar_table = Utilities.validate_search_tables(AR_DATABASE, data[0])
                is_sr_table = Utilities.validate_search_tables(SR_DATABASE, data[0])
                # Defining default values to return data
                res_ar = None
                res_sr = None
                if is_ar_table and is_sr_table:
                    # The table is in both schema, making the search in AR only
                    res_ar = AR_DATABASE.search(data[0])
                elif is_ar_table and not is_sr_table:
                    # The table is only in AR schema, making the search in AR only
                    res_ar = AR_DATABASE.search(data[0])
                elif is_sr_table and not is_ar_table:
                    # The table is only in SR schema, making the search in SR only
                    res_sr = SR_DATABASE.search(data[0])
                else:
                    # General exception. Error in DB
                    logging.error('search: Internal error of the database when deciding the search schema criteria')
                    return Response("Database internal error, contact with administrator", 500)
                # Return the results of the performed search
                res = res_ar or res_sr
                if res.count() > 0:
                    # We have data to show
                    logging.info("search: the username: %s requests a search without size of %s elements" %
                                 (USER.username, res.count()))
                    # Returning the results
                    # TODO find a solution to serialize datetimes
                    return jsonify(json_list=res.all())
                else:
                    logging.info("search: the username: %s requests a search without results" % USER.username)
                    return Response("The search query doesn't return any result"), 200
            else:
                logging.error("add_action: there is a problem with entered data")
                # Data is not valid, check the problem
                if "duplicated" in msg:
                    # Data sent is duplicated.
                    return Response(msg), 409
                else:
                    # Standard Error
                    return Response(msg), 400
        else:
            return Response("This method doesn't allow list of JSON", 400)


################################################################################

@app.route('/api/<version>/add_action', methods=['POST'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
@required_roles('administrator', 'system', 'Pilot source system')
def add_action(version=app.config['ACTUAL_API']):
    """
    Add a new LEA (Low Elementary Action) into database.
    
    The JSON structure must be in a defined format called Common Data format as:

    {
        "action": "eu:c4a:POI_EXIT",
        "user": "eu:c4a:user:9",
        "pilot": "LCC",
        "location": "eu:c4a:Pharmacy:Vanilla123",
        "position": "38.976908 22.724375",
        "timestamp": "2015-05-20T07:08:41.013+03:00",
        "payload": {
            "instance_id": "1287"
        },
        "rating": 0.45,
        "data_source_type": [ "sensors", "external_dataset" ],
        "extra": {
            "pilot_specific_field": "some value"
        }
    }

    :param basestring version: Api version

    :return: Different kind of HTML codes explaining if the action was successful
    """

    if Utilities.check_connection(app, version):
        # We created a list of Python dict.
        data = _convert_to_dict(request.json)
        msg = Utilities.check_add_action_data(AR_DATABASE, data)
        if data and not msg and USER:
            # User and data are OK. save data into DB
            res_ar = AR_DATABASE.add_action(data)
            res_sr = SR_DATABASE.add_action(data)
            if res_ar and res_sr:
                logging.info("add_action: the username: %s adds new action into database" % USER.username)
                return Response('Data stored in database OK\n'), 200
            else:
                logging.error("add_action: the username: %s failed to store data into database. 500" % USER.username)
                return "There is an error in DB", 500
        else:
            logging.error("add_action: there is a problem with entered data")
            # Data is not valid, check the problem
            if "duplicated" in msg:
                # Data sent is duplicated.
                return Response(msg), 409
            else:
                # Standard Error
                return Response(msg), 400


@app.route('/api/<version>/add_activity', methods=['POST'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
@required_roles('administrator', 'system', 'Pilot source system')
def add_activity(version=app.config['ACTUAL_API']):
    """
    Adds a new activity into the system


    An example in JSON could be:


    {
        "activity": "LeaveHouse",
        "user": "eu:c4a:user:9",
        "pilot": "LCC",
        "start_time": "2018-04-20T07:08:41.013+03:00",
        "end_time": "2018-05-20T07:08:41.013+03:00",
        "duration": 23232323,
        "payload": [{
            "action": "eu:c4a:POI_EXIT",
            "location": "eu:c4a:Pharmacy:Vanilla123",
            "timestamp": "2015-05-20T07:08:41.013+03:00",
            "position": "38.976908 22.724375"
        }, {
            "action": "eu:c4a:POI_ENTER",
            "location": "eu:c4a:Shop:Ermou96",
            "timestamp": "2014-05-20T07:08:41.013+03:00",
            "position": "37.976908 23.724375"
        }, {
            "action": "eu:c4a:APPLIANCE_ON",
            "location": "eu:c4a:Room:number23",
            "timestamp": "2012-05-20T07:08:41.013+03:00",
            "position": "42.986908 33.724375"
        }
                   ],
        "data_source_type": ["sensors", "external_dataset"]
    }

    :param basestring version: Api version

    :return: Response of the request
    """
    if Utilities.check_connection(app, version):
        data = _convert_to_dict(request.json)
        msg = Utilities.check_add_activity_data(AR_DATABASE, data)
        if data and not msg and USER:
            # User and data are OK. save data into DB
            res_ar = AR_DATABASE.add_activity(data)
            res_sr = SR_DATABASE.add_activity(data)
            if res_ar and res_sr:
                logging.info("add_activity: the username: %s adds new activity into database" % USER.username)
                return Response('Data stored in database OK\n'), 200
            else:
                logging.error("add_activity: %s failed to store data into database. 500" % USER.username)
                return Response("There is an error in DB"), 500
        else:
            logging.error("add_activity: there is a problem with entered data")
            # Data is not valid, check the problem
            if "duplicated" in msg:
                # Data sent is duplicated.
                return Response(msg), 409
            else:
                # Standard Error
                return Response(msg), 400


@app.route('/api/<version>/add_new_activity', methods=['POST'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
@required_roles('administrator')
def add_new_activity(version=app.config['ACTUAL_API']):
    """
    Adds a new value into the codebook of activities. The activity must not exist previously in database

    {
        "activity": "LeaveHouse",
        "description": "User leave the house",      # OPTIONAL VALUE
        "instrumental": true
    }

    :param basestring version: Api version

    :return: Response of the API
    """
    if Utilities.check_connection(app, version):
        data = _convert_to_dict(request.json)
        msg = Utilities.check_add_new_activity_data(AR_DATABASE, data)
        if data and not msg and USER:
            # User and data are OK. save data into DB
            res_ar = AR_DATABASE.add_new_activity(data)
            res_sr = SR_DATABASE.add_new_activity(data)
            if res_ar and res_sr:
                logging.info("add_new_activity: the username: %s adds new activity into database" % USER.username)
                return Response('Data stored in database OK\n'), 200
            else:
                logging.error(
                    "add_new_activity: the username: %s failed to store data into database. 500" % USER.username)
                return Response("There is an error in DB"), 500
        else:
            logging.error("add_new_activity: there is a problem with entered data")
            # Data is not valid, check the problem
            if "duplicated" in msg:
                # Data sent is duplicated.
                return Response(msg), 409
            else:
                # Standard Error
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

    :param basestring version: Api version

    :return: Response of the API
    """

    # TODO think about put pilot as an optional field.

    if Utilities.check_connection(app, version):
        data = _convert_to_dict(request.json)
        # check the JSON data
        msg = Utilities.check_add_new_user_data(AR_DATABASE, data)
        if data and not msg and USER:
            # User and entered data are OK. save new user into DB
            res_ar = AR_DATABASE.add_new_user_in_system(data)
            res_sr = SR_DATABASE.add_new_user_in_system(data)
            if res_ar and res_sr:
                logging.info("add_new_user: the username: %s adds new user into database" % USER.username)

                return Response('The user(s) are registered successfully in the system', 200)
            else:
                logging.error("add_new_user: %s failed to store data into database. 500" % USER.username)
                return Response("There is an error in DB"), 500
        else:
            logging.error("add_new_user: there is a problem with entered data")
            # Data is not valid, check the problem
            if "duplicated" in msg:
                # Data sent is duplicated.
                return Response(msg), 409
            else:
                # Standard Error
                return Response(msg), 400


@app.route('/api/<version>/add_care_receiver', methods=['POST'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
@required_roles('administrator', 'system', 'Pilot source system')
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
    
    :param base version: Api version

    :return: Response of the request
    """
    if Utilities.check_connection(app, version):
        data = _convert_to_dict(request.json)
        # Checking if INPUT json is OK
        msg = Utilities.check_add_care_receiver_data(AR_DATABASE, data)
        if data and not msg and USER:
            # User and entered data are OK. save new user into DB
            res_ar = AR_DATABASE.add_new_care_receiver(data, USER.id)
            res_sr = SR_DATABASE.add_new_care_receiver(data, USER.id)
            if res_ar and res_sr:
                # We only return one value, because both database has the same IDS
                logging.info(
                    "add_care_receiver: the username: %s adds new user care receiver into database" % USER.username)
                return jsonify(res_ar)
            else:
                logging.error("add_care_receiver: %s failed to store data into database. 500" % USER.username)
                return Response("There is an error in DB"), 500
        else:
            logging.error("add_care_receiver: there is a problem with entered data")
            # Data is not valid, check the problem
            if "duplicated" in msg:
                # Data sent is duplicated.
                return Response(msg), 409
            else:
                # Standard Error
                return Response(msg), 400


@app.route('/api/<version>/clear_user', methods=['POST'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
@required_roles('administrator', 'system')
def clear_user(version=app.config['ACTUAL_API']):
    """
    Clear all data related to a list of defined users. This is only can be performed by an administration
    level role. The administrator needs to define the username and its role.

    An example in JSON could be:

    {
        "id": "eu:c4a:pilot:lecce:user:12345",
    }

    :param basestring version: Api version

    :return: Response of the request
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
@required_roles('administrator', 'system', 'Pilot source system')
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

    :param basestring version: Api version

    :return: Response of the request

    """
    if Utilities.check_connection(app, version):
        # We created a list of Python dict.
        data = _convert_to_dict(request.json)
        msg = Utilities.check_add_measure_data(SR_DATABASE, data)
        if data and not msg and USER:
            # User and data are OK. save data into DB
            res = SR_DATABASE.add_measure(data)
            if res:
                logging.info("add_measure: the username: %s adds new action into database" % USER.username)
                return Response('add_measure: data stored in database OK\n'), 200
            else:
                logging.error("add_measure: the username: %s failed to store data into database. 500" % USER.username)
                return "There is an error in DB", 500
        else:
            logging.error("add_measure: there is a problem with entered data")
            # Data is not valid, check the problem
            if "duplicated" in msg:
                # Data sent is duplicated.
                return Response(msg), 409
            else:
                # Standard Error
                return Response(msg), 400


@app.route('/api/<version>/add_eam', methods=['POST'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
@required_roles('administrator', 'system', 'Pilot source system')
def add_eam(version=app.config['ACTUAL_API']):
    """
    This endpoint allows to pilots insert information about related EAMS from different type of activities.

    It allow to Expert Activity Model, have an input access to discover new activities based on user performed actions.


    An example in JSON could be:

    {
    	"name": "mad:8:makedinner",
        "user": "eu:c4a:user:12345",                            # OPTIONAL user information. Default: Pilot Id
        "activity": "AnsweringPhone",                           # This must exist previously
        "locations": ["Kitchen", "Office", "Bedroom"],
        "transformed_action": ["KitchenPIR", "BedroomPIR"],     # Transformed actions of the new EAM
        "duration": 120,                                        # Duration time
        "start": [
            ["12:00", "12:05"],
            ["20:00", "20:10"]
        ]
    }

    :param basestring version: Api version

    :return: Response of the request
    """

    if Utilities.check_connection(app, version):
        # We created a list of Python dict.
        data = _convert_to_dict(request.json)
        msg = Utilities.check_add_eam_data(AR_DATABASE, data, USER.user_in_role[0].pilot_code or 'lcc')
        if data and not msg and USER:
            # The user data are correct. We proceed to insert it into DB
            res = AR_DATABASE.add_eam(data, USER.id)
            if res:
                logging.info("add_eam: the username: %s adds new EAM into database" % USER.username)
                return Response('add_eam: data stored in database OK\n'), 200
            else:
                logging.error("add_eam: the username: %s failed to store data into database. 500" % USER.username)
                return "There is an error in DB", 500
        else:
            logging.error("add_eam: there is a problem with entered data")
            # Data is not valid, check the problem
            if "duplicated" in msg:
                # Data sent is duplicated.
                return Response(msg), 409
            else:
                # Standard Error
                return Response(msg), 400


@app.route('/api/<version>/add_frailty_status', methods=['POST'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
@required_roles('administrator', 'system', 'Pilot source system')
def add_frailty_status(version=app.config['ACTUAL_API']):
    """
    This endpoint allows to geriatricians, add a ground truth of the status of each citizen, by selecting their status

    * Non-Frail
    * Pre-Frail
    * Frail

    An example of JSON could be

    {
          "user": "eu:c4a:user:9",
          "interval_start": "2014-01-20T00:00:00.000+08:00",
          "duration": "MON",
          "condition": "frail",
          "notice": "Jon Doe is the best"
    }


    :param basestring version: Api version

    :return: Response of the request
    """

    if Utilities.check_connection(app, version):
        # We created a list of Python dict.
        data = _convert_to_dict(request.json)
        msg = Utilities.check_add_frailty_status(SR_DATABASE, data, USER.user_in_role[0].pilot_code or 'lcc')
        if data and not msg and USER:
            # Data entered ok, executing the needed method to insert data in DB
            res = SR_DATABASE.add_frailty_status(data, USER.id)
            if res:
                logging.info("add_frailty_status: the username: %s adds new Frailty_Status into database" % USER.username)
                return Response('add_frailty_status: data stored in database OK\n'), 200
            else:
                logging.error("add_frailty_status: the username: %s failed to store data into database. 500" % USER.username)
                return "There is an error in DB", 500
        else:
            logging.error("add_frailty_status: there is a problem with entered data")
            # Data is not valid, check the problem
            if "duplicated" in msg:
                # Data sent is duplicated.
                return Response(msg), 409
            else:
                # Standard Error
                return Response(msg), 400

@app.route('/api/<version>/add_factor', methods=['POST'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
@required_roles('administrator', 'system', 'Pilot source system')
def add_factor(version=app.config['ACTUAL_API']):
    """
    This method allows to insert data to geriatric factor table directly


    {
          "user": "eu:c4a:user:9",
          "pilot": "lcc",
          "interval_start": "2014-01-20T00:00:00.000+08:00",
          "duration": "MON",
          "factor": "GES",
          "score": 2,
          "notice": "Jon Doe is the best"
    }


    :param basestring version: Api version

    :return: Response of the request
    """

    """
    if Utilities.check_connection(app, version):
        # We created a list of Python dict.
        data = _convert_to_dict(request.json)
        msg = Utilities.check_add_factor(SR_DATABASE, data)
        if data and not msg and USER:
            # Data entered ok, executing the needed method to insert data in DB
            res = SR_DATABASE.add_factor(data, USER.id)
            if res:
                logging.info("add_factor: the username: %s adds new factor into database" % USER.username)
                return Response('add_frailty_status: data stored in database OK\n'), 200
            else:
                logging.error("add_factor: the username: %s failed to store data into database. 500" % USER.username)
                return "There is an error in DB", 500
        else:
            logging.error("add_factor: there is a problem with entered data")
            # Data is not valid, check the problem
            if "duplicated" in msg:
                # Data sent is duplicated.
                return Response(msg), 409
            else:
                # Standard Error
                return Response(msg), 400

    """

    return "Not implemented yet", 501




@app.route('/api/<version>/commit_measure', methods=['GET'])
@limit_content_length(MAX_LENGHT)
@auth.login_required
@required_roles('Pilot source system')
def commit_measure(version=app.config['ACTUAL_API']):
    """
    This method executes and external program that makes the needed calculations in SR schema and
    updates some tables


    :param basestring version: API version

    :return: Response of the request
    """
    if Utilities.check_version(app=app, p_ver=version) and USER:
        # Calling to external java jar file to update database data
        res = SR_DATABASE.commit_measure(USER)
        if res:
            logging.info("commit_measure: data commit successfully")
            return Response('Your measures are successfully saved and committed in database\n'), 200
        else:
            logging.error("commit_measure: failed to commit measures data in DB")
            return Response('FAILED: the commit script was encountered an error. Contact with administrator'), 500


"""
TODO endpoints

· add_measure: to add conventional measures, such as SHOP_VISITS
· add_factor: (formerly add_ges) to directly add geriatric factors’ 1-5 scores (GESs or GEFs without children, like Dependence or Physical 
    Activity), bypassing computation from measures (e.g. for green factors obtained through Caregiver App manual input)
"""


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

    :param list p_requested_data: A list containing Json Strings datasets or a List of JSON dicts

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
