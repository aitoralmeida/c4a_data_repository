# -*- coding: utf-8 -*-

"""

This class has all utilities of the project. The idea is to store all checkers, and some classes than can be useful.


"""

import logging
from flask import abort, session, request
from jsonschema import validate, ValidationError
from src.packORM import tables


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

    # Todo acces level definition
    @staticmethod
    def check_session(app, p_database):
        """
        Checks if the actual user has a session cookie registered


        :param app: Flask application
        :param p_database: The database instantiation of SQL Alchemy

        :return: True if cookie is ok
                False is there isn't any cookie or cookie is bad.
        """
        if session and session.get('token', False):
            return p_database.verify_auth_token(session.get('token'), app)
        else:
            logging.error("check_connection: User session cookie is not OK, 401")
            abort(401)

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
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50
                },
                "payload": {
                    "type": "object",
                    "properties": {
                        "user": {"type": "string"},
                        "position": {"type": "string"}
                    },
                    "required": ["user", "position"]
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
                            "maxLength": 40
                        },
                    },
                    "required": ["pilot"]
                },
                "secret": {
                    "description": "Some aditional values",
                    "type": "string",
                },
            },
            "required": ["action", "location", "payload", "timestamp", "rating", "extra", "secret"]
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
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "indoor": {"type": "boolean"}
                    },
                    "required": ["name", "indoor"]
                },
                "pilot": {
                    "description": "the name of the city where is the location",
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 40
                }
            },
            "required": ["activity_name", "activity_start_date", "activity_end_date", "since", "house_number",
                         "location",
                         "pilot"]
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
    def check_add_new_user(p_data):
        """
        Check if data is ok and if the not nullable values are filled.

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
                "type": {
                    "description": "The stakeholder needed by the system",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 20
                }
            },
            "required": [
                "username",
                "password",
                "type"
            ]
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
    def check_search(p_database, p_data):
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
            ]
        }

        try:
            if type(p_data) is list:
                for data in p_data:
                    validate(data, schema)
                    # Once data is validated, we are going to check if tables ARE OK
                    if not Utilities.validate_search_tables(p_database, data):
                        logging.error("User entered an invalid table name: %s" % tables)
                        raise ValidationError
            else:
                validate(p_data, schema)
                # Once data is validated, we are going to check if tables ARE OK
                if not Utilities.validate_search_tables(p_database, p_data):
                    logging.error("User entered an invalid table name: %s" % tables)
                    raise ValidationError

            res = True
        except ValidationError:
            logging.error("The schema entered by the user is invalid")

        return res

    # TODO, here, we are goingi to DEFINE some filter of users tables. Define tables with some access level.
    @staticmethod
    def validate_search_tables(p_database, p_data):
        """
        This class check if the current data set has valid tables to make a search in database

        :param p_database: The database instantiation of SQL Alchemy
        :param p_data: User sent data

        :return: True o False if tables are ok
        """
        res = False
        if p_data and p_data.get('table', False):
            table = p_data['table'].lower() or None  # lowering string cases
            current_tables = p_database.get_tables()            # TODO define next a filter algorithm.
            if table in current_tables:
                res = True
        return res
