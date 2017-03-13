# -*- coding: utf-8 -*-

"""

This class has all utilities of the project. The idea is to store all checkers, and some classes than can be useful.


"""

import logging
from flask import abort, session, request
from jsonschema import validate, ValidationError

__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2016, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"


class Utilities(object):
    # CHECKS RELATED
    @staticmethod
    def check_connection(app, p_ver):
        """
        Make a full check of all needed data

        :param app: Flask application
        :param p_ver: Actual version of the API

        :return: True if everithing is OK.
                An error code (abort) if something is bad
        """
        # Check if the Api level is ok
        if Utilities.check_version(app=app, p_ver=p_ver):
            # check if the content type is JSON
            if Utilities.check_content_type():
                return True
            else:
                logging.error("check_connection: Content-type is not JSON serializable, 400")
                abort(400)
        else:
            logging.error("check_connection, Actual API is WRONG, 404")
            abort(404)

    @staticmethod
    def check_content_type():
        """
        Checks if actual content_type is OK

        :return: True if everything is ok.
                False if something is wrong
        """
        content_type_ok = False
        # Check if request headers are ok
        if request.headers['content-type'] == 'application/json':
            content_type_ok = True
        return content_type_ok

    @staticmethod
    def check_version(app, p_ver):
        """
        Check if we are using a good api version

        :param app: Flask application
        :param p_ver: API version

        :return:  True or False if api used is ok.
        """
        api_good_version = False
        if p_ver in app.config['AVAILABLE_API']:
            api_good_version = True
        return api_good_version

    @staticmethod
    def check_add_action_data(p_data):
        """
        Check if data is ok and if the not nullable values are filled.


        :param p_data: data from the user.
        :return: True or False if data is ok.
        """

        res = False
        # Defining schema to be compared with entered data
        schema = {
            "title": "Add action schema",
            "type": "object",
            "properties": {
                "action": {
                    "description": "the name of the action",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50
                },
                "location": {
                    "description": "location of the performed action",
                    "anyOf": [
                        {
                            "type": "object",
                            "properties": {
                                "lat": {
                                    "type": "string",
                                    "minLength": 1,
                                },
                                "long": {
                                    "type": "string",
                                    "minLength": 1,
                                }
                            },
                            "required": ["lat", "long"]
                        },
                        {
                            "type": "string",
                            "minLength": 3,
                            "maxLength": 50
                        }
                    ]
                },
                "payload": {
                    "type": "object",
                    "properties": {
                        "user": {"type": "string"},
                        "instanceID": {
                            "description": "an ID required to associate correlated LEA records, such as 'start-stop' "
                                           "LEA instances",
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 4
                        }
                    },
                    "required": ["user", "instanceID"]
                },
                "timestamp": {
                    "description": "The time when de action was performed",
                    "type": "string",
                    # "format": "date-time",   # ASK To know if sended data is in RFC 3339, section 5.6. to use this format
                    "minLength": 3,
                    "maxLength": 50
                },
                "rating": {
                    "description": "Uncertainty value of the action",
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                },
                "extra": {
                    "type": "object",
                    "properties": {
                        "pilot": {
                            "description": "the name of the city where is the location",
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 40,
                            "enum": [
                                "madrid",
                                "lecce",
                                "singapore",
                                "montpellier",
                                "athens",
                                "birmingham"
                            ]
                        },
                    },
                    "required": ["pilot"]
                },
                "secret": {
                    "description": "Some aditional values",
                    "type": "string",
                },
            },
            "required": ["action", "payload", "timestamp", "rating", "extra", "secret"],
            "additionalProperties": False
        }

        try:
            if type(p_data) is list:
                # We have a list of dicts
                for data in p_data:
                    validate(data, schema)
            else:
                validate(p_data, schema)
            res = True
        except ValidationError:
            logging.error("The schema entered by the user is invalid")

        return res

    @staticmethod
    def check_add_activity_data(p_data):
        """
        Check if data is ok and if the not nullable values are filled.

        The user needs to send all data, if the location values are indoor it  must provide a valid house number, otherwise
        it must send a house number with zero value. The idea is to avoid nullable values in DB.

        :param p_data: User sent data

        :return: True or False if data is ok
        """

        res = False
        # Defining schema to be compared with entered data
        schema = {
            "title": "Add activity schema",
            "type": "object",
            "properties": {
                "activity_name": {
                    "description": "The name of the current activity",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50
                },
                "activity_start_date": {
                    "description": "The start date of the executed activity",
                    "type": "string"
                },
                "activity_end_date": {
                    "description": "The final date of the executed activity",
                    "type": "string"
                },
                "since": {
                    "description": "A measure to make some calculations based on activity",
                    "type": "string"
                },
                "house_number": {
                    "description": "The number of house in case of indoor is true",
                    "type": "integer",
                    "minimum": 0
                },
                "location": {
                    "description": "location of the performed action",
                    "anyOf": [
                        {
                            "type": "object",
                            "properties": {
                                "lat": {
                                    "type": "string",
                                    "minLength": 1,
                                },
                                "long": {
                                    "type": "string",
                                    "minLength": 1,
                                }
                            },
                            "required": ["lat", "long"]
                        },
                        {
                            "type": "string",
                            "minLength": 3,
                            "maxLength": 50
                        }
                    ]
                },
                "indoor": {
                    "description": "Defines if the activity is inside a building or not",
                    "type": "boolean",
                },
                "pilot": {
                    "description": "the name of the city where is the location",
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 40,
                    "enum": [
                        "madrid",
                        "lecce",
                        "singapore",
                        "montpellier",
                        "athens",
                        "birmingham"
                    ]
                }
            },
            "required": ["activity_name", "activity_start_date", "activity_end_date", "since", "house_number",
                         "location", "indoor", "pilot"],
            "additionalProperties": False
        }

        try:
            if type(p_data) is list:
                # We have a list of dicts
                for data in p_data:
                    validate(data, schema)
            else:
                validate(p_data, schema)
            res = True
        except ValidationError:
            logging.error("The schema entered by the user is invalid")

        return res

    @staticmethod
    def check_add_new_user_data(p_database, p_data):
        """
        Check if data is ok and if the not nullable values are filled.

        :p_p_database: The database instance to call
        :param p_data: User sent data

        :return:  True or False if data is ok
        """
        res = False
        schema = {
            "title": "Add new user in system schema",
            "type": "object",
            "properties": {
                "username": {
                    "description": "The username of the actual user",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 15
                },
                "password": {
                    "description": "The password for the user",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 45
                },
                "user": {
                    "description": "The id of the user that is going to have an access",
                    "type": "string",
                    "pattern": "urn:[a-z]{2}:c4a:[a-z]{5}:[a-z]{5,10}:user:[1-9]{1,10}$"
                },
                "roletype": {
                    "description": "The role name of registered user",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 20,
                    "enum": [
                        "care_giver",
                        "care_receiver",
                        "geriatrician",
                        "municipality_representative",
                        "researcher",
                        "application_developer",
                        "administrator"
                    ]
                }
            },
            "required": [
                "username",
                "password",
                "user",
                "roletype"
            ],
            "additionalProperties": False
        }

        try:
            if type(p_data) is list:
                # We have a list of dicts
                for data in p_data:
                    validate(data, schema)
                    if Utilities.validate_user_registered(p_database, data):
                        # The user exist in the system
                        logging.error("The entered username is duplicated: %s", data['username'])
                        raise ValidationError("Duplicate username: %s", data["username"])
                    elif Utilities.validate_user_in_role(p_database, data):
                        # The user hasn't any acess in the system or there isnt any user with that ID
                        logging.error("The user entered has already a username and password in the system")
                        raise ValidationError("The user has already a username/password configured")
            else:
                # single user to be registered in database
                validate(p_data, schema)
                if Utilities.validate_user_registered(p_database, p_data):
                    # The user exist in the system
                    logging.error("The entered username is duplicated: %s", p_data['username'])
                    raise ValidationError("Duplicate username: %s", p_data["username"])
                elif Utilities.validate_user_in_role(p_database, p_data):
                    # The user hasn't any acess in the system or there isnt any user with that ID
                    logging.error("The user entered has already a username and password in the system")
                    raise ValidationError("The user has already a username/password configured")
            res = True
        except ValidationError:
            logging.error("The schema entered by the user is invalid")

            # TODO we need to return error messages to the API to use ABORT personal meesages

        return res

    @staticmethod
    def check_clear_user_data(p_data):
        """
        Check if data is ok

        :param p_data: User sent data

        :return:  True or False if data is ok
        """
        res = False
        schema = {
            "title": "Clear all data related to user in the system",
            "type": "object",
            "properties": {
                "id": {
                    "description": "The id of the user in role in system",
                    "type": "string",
                    "minLength": 10,
                    "maxLength": 75
                }
            },
            "required": [
                "id"
            ],
            "additionalProperties": False
        }

        try:
            if type(p_data) is list:
                # We have a list of dicts
                for data in p_data:
                    validate(data, schema)
            else:
                validate(p_data, schema)
            res = True
        except ValidationError:
            logging.error("The schema entered by the user is invalid")

        return res

    @staticmethod
    def check_add_measure_data(p_data):
        """

        Check if add_measure data is entered ok with required values

        :param p_data: User data
        :return:
        """
        res = False

        schema = {
            "title": "Add measure schema",
            "type": "object",
            "properties": {
                "gef": {
                    "description": "The name of the type of measure to enter",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50
                },
                "ges": {
                    "description": "The sub-type of measure to enter",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50
                },
                "payload": {
                    "description": "contains relative information about the entered GEF/GES into the system",
                    "type": "object",
                    "properties": {
                        # Required parameters for all combinations of GEF/GES
                        "user": {
                            "type": "string",
                            "minLength": 3,
                            "maxLength": 50
                        },
                        "date": {
                            "type": "string",
                            # "format": "date-time",   # ASK To know if sended data is in RFC 3339, section 5.6. to use this format
                            "minLength": 3,
                            "maxLength": 50
                        },
                    },
                    "required": ["user", "date"],
                },
                "timestamp": {
                    "description": "The time when de action was performed",
                    "type": "string",
                    # "format": "date-time",   # ASK To know if sended data is in RFC 3339, section 5.6. to use this format
                    "minLength": 3,
                    "maxLength": 50
                },
                "extra": {
                    "description": "contains the information about what pilot performs the action",
                    "type": "object",
                    "properties": {
                        "pilot": {
                            "description": "the name of the city when the measure is performed",
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 40,
                            "enum": [
                                "madrid",
                                "lecce",
                                "singapore",
                                "montpellier",
                                "athens",
                                "birmingham"
                            ]
                        }
                    },
                    "required": ["pilot"]
                }
            },
            "required": ["gef", "ges", "payload", "timestamp", "extra"],
            "additionalProperties": False
        }

        try:
            if type(p_data) is list:
                # We have a list of dicts
                for data in p_data:
                    validate(data, schema)
            else:
                validate(p_data, schema)
            res = True
        except ValidationError:
            logging.error("The schema entered by the user is invalid")
        return res

    @staticmethod
    def check_search_data(p_database, p_data):
        """
        Check if search data is ok and evaluates what is the best table that fits with search criteria

        :param p_database: The database instantiation of SQL Alchemy
        :param p_data: User sent data

        :return:    True if all is OK
                    False if there is a problem
        """
        res = False

        schema = {
            "title": "Search datasets schema validator",
            "type": "object",
            "properties": {
                "table": {
                    "description": "The name of the target table to make the search",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50
                },
                "criteria": {
                    "description": "The user search criteria",
                    "type": "object"
                },
                "limit": {
                    "description": "The limit of the query",
                    "type": "integer",
                    "minimum": 0
                },
                "offset": {
                    "description": "The offset of the query",
                    "type": "integer",
                    "minimum": 0
                },
                "order_by": {
                    "description": "The name of the target table to make the search",
                    "type": "string",
                    "maxLength": 4
                }
            },
            "required": [
                "table",
                "criteria"
            ],
            "additionalProperties": False
        }

        try:
            if type(p_data) is list:
                for data in p_data:
                    validate(data, schema)
                    # Once data is validated, we are going to check if tables ARE OK
                    if not Utilities.validate_search_tables(p_database, data):
                        logging.error("User entered an invalid table name: %s" % p_database.get_tables)
                        raise ValidationError("Invalid table name: %s", data['table'])
            else:
                validate(p_data, schema)
                # Once data is validated, we are going to check if tables ARE OK
                if not Utilities.validate_search_tables(p_database, p_data):
                    logging.error("User entered an invalid table name: %s" % p_database.get_tables)
                    raise ValidationError("Invalid table name: %s", p_data['table'])

            res = True
        except ValidationError:
            logging.error("The schema entered by the user is invalid")

        return res

    # TODO review this search method
    @staticmethod
    def validate_search_tables(p_database, p_one_data):
        """
        This method checks if the current data set has valid tables to make a search in database

        :param p_database: The database instantiation of SQL Alchemy
        :param p_one_data: User sent data

        :return: True o False if tables are ok
        """
        res = False
        if p_one_data and p_one_data.get('table', False):
            table = p_one_data['table'].lower() or None  # lowering string cases
            current_tables = p_database.get_tables()
            if table in current_tables:
                res = True
        return res


    @staticmethod
    def validate_user_registered(p_database, p_one_data):
        """
        This method checks if the current data set has a duplicate username in database.

        :param p_database: The database instantiation of SQL Alchemy
        :param p_one_data: User sent data

        :return: True if the user exists in the system
                  False if the user not exist in the system
        """
        res = False
        if p_one_data and p_one_data.get('username', False):
            username = p_one_data['username'].lower() or None  # lowering string cases
            # Get current registered users
            res = p_database.check_username(username)
        return res


    @staticmethod
    def validate_user_in_role(p_database, p_one_data):
        """
        Give the user information, check if it has already a username/password configured.

        If the user has not a username/password configured or if it not exist in the system, then this method will
        return a True state status,

        :param p_database: The database instance
        :param p_one_data: The user information (ID)
        :return: True if the user hasn't a username/password configured (Access in user registered) or if the user id
        """
        res = False
        if p_one_data and p_one_data.get('user', False):
            user_in_role = p_one_data['user'].lower() or None  # lowering string cases
            # Get current registered users
            res = p_database.check_user_access(user_in_role)
        return res


    @staticmethod
    def write_log_info(app, p_message):
        """
        Write info log into a file

        :param app: Flask application
        :param p_message: Message to send to log file

        """
        app.logger.info(p_message)

    @staticmethod
    def write_log_warning(app, p_message):
        """
        Write info log into a file

        :param app: Flask application
        :param p_message: Message to send to log file

        """
        app.logger.warning(p_message)

    @staticmethod
    def write_log_error(app, p_message):
        """
        Write info log into a file

        :param app: Flask application
        :param p_message: Message to send to log file

        """
        app.logger.error(p_message)
