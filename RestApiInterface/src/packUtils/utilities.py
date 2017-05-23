# -*- coding: utf-8 -*-

"""

This class has all utilities of the project. The idea is to store all checkers, and some classes than can be useful.


"""

import logging
from collections import Counter
from flask import abort, session, request
from jsonschema import validate, ValidationError, FormatChecker

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
    def check_add_action_data(p_database, p_data):
        """
        Check if data is ok and if the not nullable values are filled.


        :param p_data: data from the user.
        :return: True or False if data is ok.
        """

        res = False
        msg = None
        # Defining schema to be compared with entered data
        schema = {
            "title": "Add action schema",
            "type": "object",
            "properties": {
                "action": {
                    "description": "the name of the action",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50,
                    "pattern": "^eu:c4a:[a-z,A-Z]{3,15}_[a-z,A-Z]{2,15}$",
                },
                "user": {
                    "description": "The user in role who performs the registered action",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50,
                    "pattern": "^eu:c4a:user:[0-9]{1,15}$",
                },
                "pilot": {
                    "description": "the name of the city where is the location",
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 10,
                    "enum": [
                        "ATH", "BHX", "LCC", "MAD", "MPL", "SIN",
                        "ath", "bhx", "lcc", "mad", "mpl", "sin",
                    ]
                },
                "location": {
                    "description": "Semantic location of the performed action",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50,
                    "pattern": "^eu:c4a:[a-z,A-Z,0-9]{3,25}:[a-z,A-Z,0-9]{1,30}$",
                },
                "position": {
                    "description": "The exact position given in Lat/Long format",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50
                },
                "timestamp": {
                    "description": "The time when de action was performed",
                    "type": "string",
                    "format": "date-time",
                    "minLength": 3,
                    "maxLength": 45
                },
                "payload": {
                    "description": "In this field there are send the optional parameters of the LEA",
                    "type": "object",
                    "additionalProperties": True
                },

                "data_source_type": {
                    "description": "how the action has been decided or imported",
                    "type": "array",
                    "uniqueItems": True,
                    "items": {
                        "type": "string",
                        "enum": [
                            "sensors",
                            "city_dataset",
                            "external_dataset",
                            "manual_input",
                        ],
                    },
                },

                "extra": {
                    "description": "Additional information given by the Pilot in the LEA",
                    "type": "object",
                    "additionalProperties": True,
                },
            },
            "required": ["action", "user", "pilot", "location", "position", "timestamp", "payload", "data_source_type"],
            "additionalProperties": False,
        }

        try:
            # Obtaining the list of action from database
            list_of_actions = p_database.get_action_name()
            # Extracting actions from the two level lists
            # checking data
            if type(p_data) is list:
                # We have a list of dicts
                for data in p_data:
                    validate(data, schema, format_checker=FormatChecker())
                    # We are going to validate if inserted actions are OK
                    if not data['action'].split(':')[-1].lower() in list_of_actions:
                        # Raising
                        logging.error("The action inserted doesn't exist in the system: %s" % data['action'])
                        raise ValidationError("The action inserted doesn't exist in the system: %s" % data['action'])
                    elif not Utilities.validate_user_pilot(p_database, data['user'].split(':')[-1].lower(),
                                                           data['pilot'].lower()):
                        logging.error("The entered user pilot is incorrect: %s", data['user'])
                        raise ValidationError("The entered user pilot is incorrect: %s", data['user'])
            else:
                validate(p_data, schema, format_checker=FormatChecker())
                # We are going to validate if inserted actions are OK
                if not p_data['action'].split(':')[-1].lower() in list_of_actions:
                    # Raising
                    logging.error("The action inserted doesn't exist in the system: %s" % p_data['action'])
                    raise ValidationError("The action inserted doesn't exist in the system: %s" % p_data['action'])
                elif not Utilities.validate_user_pilot(p_database, p_data['user'].split(':')[-1].lower(),
                                                       p_data['pilot'].lower()):
                    logging.error("The entered user pilot is incorrect: %s", p_data['user'])
                    raise ValidationError("The entered user pilot is incorrect: %s", p_data['user'])

            res = True
        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message
        return res, msg

    @staticmethod
    def check_add_activity_data(p_database, p_data):
        """
        Check if data is ok and if the not nullable values are filled.

        The user needs to send all data, if the location values are indoor it  must provide a valid house number, otherwise
        it must send a house number with zero value. The idea is to avoid nullable values in DB.

        :param p_data: User sent data

        :return: True or False if data is ok
        """

        res = False
        msg = None
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
                "activity_description": {
                    "description": "The description of the activity"
                },
                "instrumental": {
                    "description": "Defines if an activity is a Basic or a instrumental Activity",
                    "type": "boolean"
                },
                "house_number": {
                    "description": "The number of house in case of indoor is true",
                    "type": "integer",
                    "minimum": 0
                },
                "location": {
                    "description": "Semantic location of the performed action",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50,
                    "pattern": "^eu:c4a:[a-z,A-Z,0-9]{3,25}:[a-z,A-Z,0-9]{1,30}$",
                },
                "indoor": {
                    "description": "Defines if the activity is inside a building or not",
                    "type": "boolean",
                },
                "pilot": {
                    "description": "the name of the city where is the location",
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 10,
                    "enum": [
                        "ATH", "BHX", "LCC", "MAD", "MPL", "SIN",
                        "ath", "bhx", "lcc", "mad", "mpl", "sin",
                    ]
                },
            },
            "required": ["activity_name"],
            "additionalProperties": False
        }

        # TODO modify the validator when the user decide to use spatio-temporal activities (House, location...)

        try:
            if type(p_data) is list:
                # We have a list of dicts
                list_of_activities = []
                for data in p_data:
                    validate(data, schema, format_checker=FormatChecker())
                    # check if the activity exist in database or not
                    if Utilities.validate_activity(p_database, data):
                        # The activity exist already in database
                        logging.error("The entered activity is duplicated: %s", data['activity_name'])
                        raise ValidationError("The entered activity is duplicated: %s" % data['activity_name'])
                    # Appending the activity
                    list_of_activities.append(data['activity_name'])
                # We are going to search for duplicated users in the json list sent by the user
                duplicated = [k for k, v in Counter(list_of_activities).items() if v > 1]
                if len(duplicated) > 0:
                    # Raise an error for duplicated values
                    logging.error("There are are duplicated activity names in the JSON: %s" % duplicated)
                    raise ValidationError("There are are duplicated activity names in the JSON: %s" % duplicated)
            else:
                validate(p_data, schema, format_checker=FormatChecker())
                # check if the activity exist in database or not
                if Utilities.validate_activity(p_database, p_data):
                    # The activity exist already in database
                    logging.error("The entered activity is duplicated: %s", p_data['activity_name'])
                    raise ValidationError("The entered activity is duplicated: %s" % p_data['activity_name'])
            res = True
        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message
        return res, msg

    @staticmethod
    def check_add_new_user_data(p_database, p_data):
        """
        Check if data is ok and if the not nullable values are filled.

        :param p_database: The database instance to call
        :param p_data: User sent data

        :return:  True or False if data is ok
        """
        res = False
        msg = None  # A return message containing useful information
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
                    "description": "The user who the administrator wants to give an access in the system",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50,
                    "pattern": "^eu:c4a:user:[0-9]{1,15}$",
                },
                "roletype": {
                    "description": "The role name of registered user",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 20,
                    "enum": Utilities.get_user_roles(p_database)
                },
                "pilot": {
                    "description": "the name of the city where is the location",
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 10,
                    "enum": [
                        "ATH", "BHX", "LCC", "MAD", "MPL", "SIN",
                        "ath", "bhx", "lcc", "mad", "mpl", "sin",
                    ]
                },
                "valid_from": {
                    "description": "The start date of the validity of the user",
                    "type": "string",
                    "format": "date-time",
                    "minLength": 3,
                    "maxLength": 45
                },
                "valid_to": {
                    "description": "The maximum end date of the validity of the user",
                    "type": "string",
                    "format": "date-time",
                    "minLength": 3,
                    "maxLength": 45,
                },
            },
            "required": [
                "username",
                "password",
                "roletype",
                "pilot"
            ],
            "additionalProperties": False
        }


        # Todo think about using a filtered list of active users to avoid for structures

        try:
            if type(p_data) is list:
                list_of_usernames = []
                # We have a list of dicts
                for data in p_data:
                    validate(data, schema, format_checker=FormatChecker())
                    # Validating if the user exists already in the system
                    if Utilities.validate_user_registered(p_database, data):
                        # The user exist in the system
                        logging.error("The entered username is duplicated: %s", data['username'])
                        raise ValidationError("The entered username is duplicated: %s" % data['username'])
                    if data.get('user', False) and Utilities.validate_user_access(p_database, data):
                        # The user hasn't any access in the system or there inst any user with that ID
                        logging.error("The user entered has already a username and password " \
                                              "in the system or it is not exist: %s" % data['username'])
                        raise ValidationError("The user entered has already a username and password " \
                                              "in the system or it is not exist: %s" % data['username'])
                    # Appending the username
                    list_of_usernames.append(data['username'])
                # We are going to search for duplicated users in the json list sent by the user
                duplicated = [k for k, v in Counter(list_of_usernames).items() if v > 1]
                if len(duplicated) > 0:
                    # Raise an error for duplicated values
                    logging.error("There are duplicated usernames in your JSON: %s" % duplicated)
                    raise ValidationError("There are duplicated usernames in your JSON: %s" % duplicated)
            else:
                # single user to be registered in database
                validate(p_data, schema, format_checker=FormatChecker())
                if Utilities.validate_user_registered(p_database, p_data):
                    # The user exist in the system
                    logging.error("The entered username is duplicated: %s", p_data['username'])
                    raise ValidationError("The entered username is duplicated: %s" % p_data['username'])
                elif Utilities.validate_user_access(p_database, p_data):
                    # The user hasn't any acess in the system or there isnt any user with that ID
                    logging.error("The user entered has already a username and password " \
                                          "in the system: %s" % p_data['username'])
                    raise ValidationError("The user entered has already a username and password " \
                                          "in the system: %s" % p_data['username'])
            res = True
        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message
        return res, msg

    @staticmethod
    def check_add_care_receiver_data(p_database, p_data):
        """
        This method checks if the entered data by a Pilot in its JSON structure is properly configured
        
    
        :param p_database: A database instance 
        :param p_data: The needed data 
        :return: True if everything is OK
                 False is something is  KO
        """

        res = False
        msg = None
        schema = {
            "title": "Add a new care receiver in the system",
            "type": "object",
            "properties": {
                "pilot_user_source_id": {
                    "description": "The Pilot local id from their local database to identify the registered user",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 45
                },
                "valid_from": {
                    "description": "The start date of the validity of the user",
                    "type": "string",
                    "format": "date-time",
                    "minLength": 3,
                    "maxLength": 45
                },
                "valid_to": {
                    "description": "The maximum end date of the validity of the user",
                    "type": "string",
                    "format": "date-time",
                    "minLength": 3,
                    "maxLength": 45,
                },
                "username": {
                    "description": "The username of the actual user",
                    "type": "string",
                    "minLength": 4,
                    "maxLength": 15
                },
                "password": {
                    "description": "The password for the user",
                    "type": "string",
                    "minLength": 4,
                    "maxLength": 45
                },
            },
            "required": [
                "pilot_user_source_id",
                "username",
                "password",
            ],
            "additionalProperties": False
        }

        try:
            if type(p_data) is list:
                # Creatin an empty list of usernames
                list_of_usernames = []
                # We have a list of dicts
                for data in p_data:
                    # FormatChecker used to check that timestamp is correct
                    validate(data, schema, format_checker=FormatChecker())
                    if Utilities.validate_user_registered(p_database, data):
                        # The user exist in the system
                        logging.error("The entered username is duplicated: %s", data['username'])
                        raise ValidationError("Duplicate username: %s" % data["username"])
                    # adding the username to the list
                    list_of_usernames.append(data['username'])
                # We are going to search for duplicated users in the json list sent by the user
                duplicated = [k for k, v in Counter(list_of_usernames).items() if v > 1]
                if len(duplicated) > 0:
                    # Raise an error for duplicated values
                    logging.error("The user entered two or more username in the input data")
                    raise ValidationError("The user entered two or more username in the input data")
            else:
                # single user to be registered in database
                validate(p_data, schema, format_checker=FormatChecker())
                if Utilities.validate_user_registered(p_database, p_data):
                    # The user exist in the system
                    logging.error("The entered username is duplicated: %s", p_data['username'])
                    raise ValidationError("Duplicate username: %s" % p_data["username"])
            res = True
        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message

        return res, msg

    @staticmethod
    def check_clear_user_data(p_data):
        """
        Check if data is ok

        :param p_data: User sent data

        :return:  True or False if data is ok
        """

        res = False
        msg = None
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

        # TODO Insert a validation to know if the user exist already in the system. Maybe there is implemented yet

        try:
            if type(p_data) is list:
                # We have a list of dicts
                for data in p_data:
                    validate(data, schema, format_checker=FormatChecker())
            else:
                validate(p_data, schema, format_checker=FormatChecker())
            res = True
        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message
        return res, msg

    @staticmethod
    def check_add_measure_data(p_database, p_data):
        """

        Check if add_measure data is entered ok with required values

        :param p_data: User data
        :return:
        """
        res = False
        msg = None

        schema = {
            "title": "Add measure schema",
            "type": "object",
            "properties": {
                "user": {
                    "description": "The user in role who performs the registered action",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50,
                    "pattern": "^eu:c4a:user:[0-9]{1,15}$",
                },
                "pilot": {
                    "description": "the name of the city where is the location",
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 10,
                    "enum": [
                        "ATH", "BHX", "LCC", "MAD", "MPL", "SIN",
                        "ath", "bhx", "lcc", "mad", "mpl", "sin",
                    ]
                },
                "interval_start": {
                    "description": "The start time when the measure is recorded",
                    "type": "string",
                    "format": "date-time",
                    "minLength": 3,
                    "maxLength": 45
                },
                "duration": {
                    "description": "A nominal value e.g Day, Week and so on to define the end time of the measure",
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 45,
                    "enum": [
                        "DAY", "WK", "MON",
                        "day", "wk", "mon"
                    ]
                },
                "interval_end": {
                    "description": "The end time when the measure is recorded",
                    "type": "string",
                    "format": "date-time",
                    "minLength": 3,
                    "maxLength": 45
                },
                "payload": {
                    "description": "contains relative information about the entered GEF/GES into the system",
                    "type": "object",
                    "patternProperties": {
                        "^[a-z, A-Z]": {
                            "type": "object",
                            "properties": {
                                "value": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1000000,
                                    "exclusiveMinimum": True,
                                    "exclusiveMaximum": True,
                                    "multipleOf": 0.01
                                },
                                "data_source_type": {
                                    "description": "how the action has been decided or imported",
                                    "type": "array",
                                    "uniqueItems": True,
                                    "items": {
                                        "type": "string",
                                        "enum": [
                                            "sensors",
                                            "city_dataset",
                                            "external_dataset",
                                            "manual_input",
                                        ],
                                    },
                                },
                            },
                            "additionalProperties": False,
                            "required": ["value"]
                        },
                    },
                    "additionalProperties": False,
                    "minProperties": 1,
                    "maxProperties": 20
                },
                "extra": {
                    "description": "Additional information given by the Pilot in the LEA",
                    "type": "object",
                }
            },
            "additionalProperties": False,
            "oneOf": [
                {"required": ["user", "pilot", "interval_start", "extra", "duration"]},
                {"required": ["user", "pilot", "interval_start", "extra", "interval_end"]}
            ]
        }

        try:
            # Getting the list of measures
            list_of_measures = Utilities.get_measures(p_database)
            # Checking data
            if type(p_data) is list:
                # We have a list of dicts
                for data in p_data:
                    validate(data, schema, format_checker=FormatChecker())
                    # Validating measures
                    for payload in data['payload']:
                        if payload.lower() not in list_of_measures:
                            # This measure doesn't exist in database
                            logging.error("The entered measure doesn't exist: %s", payload)
                            raise ValidationError("The entered measure doesn't exist: %s", payload)
                    # Validating the user with its pilot
                    if not Utilities.validate_user_pilot(p_database, data['user'].split(':')[-1].lower(),
                                                           data['pilot'].lower()):
                        logging.error("The entered user pilot is incorrect: %s", data['user'])
                        raise ValidationError("The entered user pilot is incorrect: %s", data['user'])
            else:
                validate(p_data, schema, format_checker=FormatChecker())
                # Validating measures
                for payload in p_data['payload']:
                    if payload.lower() not in list_of_measures:
                        # This measure doesn't exist in database
                        logging.error("The entered measure doesn't exist: %s", payload)
                        raise ValidationError("The entered measure doesn't exist: %s", payload)
                # Validating the user with its pilot
                if not Utilities.validate_user_pilot(p_database, p_data['user'].split(':')[-1].lower(),
                                                       p_data['pilot'].lower()):
                    logging.error("The entered user pilot is incorrect: %s", p_data['user'])
                    raise ValidationError("The entered user pilot is incorrect: %s", p_data['user'])

            res = True
        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message
        return res, msg

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
        msg = None
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
                    validate(data, schema, format_checker=FormatChecker())
                    # Once data is validated, we are going to check if tables ARE OK
                    if not Utilities.validate_search_tables(p_database, data):
                        logging.error("User entered an invalid table name: %s" % p_database.get_tables)
                        raise ValidationError("Invalid table name: %s" % data['table'])
            else:
                validate(p_data, schema, format_checker=FormatChecker())
                # Once data is validated, we are going to check if tables ARE OK
                if not Utilities.validate_search_tables(p_database, p_data):
                    logging.error("User entered an invalid table name: %s" % p_database.get_tables)
                    raise ValidationError("Invalid table name: %s" % p_data['table'])

            res = True
        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message
        return res, msg

    @staticmethod
    def check_add_eam_data(p_database, p_data):
        """
        This method checks if the current data is properly JSON formatted with the required files


        :param p_database: The database instance
        :param p_data: The data sent by the user

        :return: True is the data is OK
                False and error state if the data is KO
        """
        res = False
        msg = None
        schema = {
            "title": "Eam database additional data validator",
            "type": "object",
            "properties": {
                "activity_name": {
                    "description": "The name of the current activity",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50
                },
                "locations": {
                    "description": "A list containing the possible locations of the EAM",
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1,
                    "uniqueItems": True,
                    "additionalProperties": False
                },
                "actions": {
                    "description": "A list containing the possible actions of the EAM",
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1,
                    "uniqueItems": True,
                    "additionalProperties": False
                },
                "duration": {
                    "description": "The total duration of the EAM",
                    "type": "integer",
                    "minimum": 0
                },
                "start": {
                    "description": "A complex list of items containing time intervals",
                    "type": "array",
                    "items": {
                        "description": "The items of the array, the should be time intervals",
                        "type": "array",
                        "items": {
                            "type": "string",
                            "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$"
                        },
                        "minItems": 2,
                        "maxItems": 2,
                        "uniqueItems": True,
                        "additionalProperties": False
                    },
                    "minItems": 1,
                    "uniqueItems": True,
                    "additionalProperties": False,
                    "required": ["items"]
                }
            },
            "required": [
                "activity_name",
                "locations",
                "actions",
                "duration",
                "start"
            ],
            "additionalProperties": False
        }

        try:
            if type(p_data) is list:
                # We have a list of dicts
                for data in p_data:
                    validate(data, schema, format_checker=FormatChecker())
                    # checking data integrity
                    res = Utilities.validate_eam(p_database, data)
                    if not res:
                        logging.error("The activity, action or location doesn't exist in database")
                        raise ValidationError("The activity, action or location doesn't exist in database")
            else:
                validate(p_data, schema, format_checker=FormatChecker())
                # checking data integrity
                res = Utilities.validate_eam(p_database, p_data)
                if not res:
                    logging.error("The activity, action or location doesn't exist in database")
                    raise ValidationError("The activity, action or location doesn't exist in database")
            res = True
        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message
        return res, msg

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

    # TODO this method needs more changes.

    @staticmethod
    def validate_user_access(p_database, p_one_data):
        """
        Giving the user information and a database connection, 
        checks if it has already a username/password configured or if it exist in the system

        If the user has already a username/password this method will return a True state
        

        :param p_database: The database instance
        :param p_one_data: The user information (ID)
        :return:    True if the user has already an access in the system
                    False if the user hasn't any access in the system.
        """
        res = False
        if p_one_data and p_one_data.get('user', False):
            user_in_role = p_one_data['user'].lower() or None  # lowering string cases
            # Converting the user data to get the ID
            user_in_role_id = int(user_in_role.split(':')[-1])
            # Get current registered users
            res = p_database.check_user_access(user_in_role_id)
        return res

    @staticmethod
    def validate_user_pilot(p_database, p_user, p_pilot):
        """
        Giving a User and Pilot, this method checks if the users exist in database and if exsit, it checks its pilot 
        code
                
        :param p_database: The database instance 
        :param p_user: The user in the system
        :param p_pilot: The pilot 
        :return: True if the user doens't exist of everything is ok
                False if something is not well.
        """

        return p_database.check_user_pilot(p_user, p_pilot)

    @staticmethod
    def validate_eam(p_database, p_one_data):
        """
        This method checks if the given element of a EAM has valid information.

        To know it we need to check the following:

            * Activiy: If the activities exist in DB
            * Actions: If the actions exist in DB
            * Locations: If the locations exist in DB

        :param p_database: The database instance
        :param p_one_data: The information about an EAM
        :return: True if the information of EAM is correct
                False if some of the EAM elements are not correct
        """
        res = False

        # checking if exist activity name
        if p_one_data and p_one_data.get('activity_name', False):
            activity_name = p_one_data['activity_name'].lower() or None
            # Check if the activity exist in DB
            res = p_database.check_activity(activity_name)

        # checking if exist action name
        if res and p_one_data and p_one_data.get('actions', False):
            # We check if the actions exist in DB
            for action_name in p_one_data['actions']:
                # GIVING an action name we check it in DB
                res = p_database.check_action(action_name.lower())
                if not res:
                    res = False  # Ensuring that result is FALSE and not NONE or whatever
                    break
        else:
            logging.error("validate_eam: some of the values are not present")
            res = False

        if res and p_one_data and p_one_data.get('locations', False):
            # We check if the locations exist in DB
            for location_name in p_one_data['locations']:
                # GIVING a location name we check it in DB
                res = p_database.check_location(location_name.lower())
                if not res:
                    res = False
                    break
        else:
            logging.error("validate_eam: some of the values are not present")
            res = False

        return res

    @staticmethod
    def validate_activity(p_database, p_one_data):
        """
        This method check in database if the current activity exist already or not to avoid
        duplicate insertion from methods like add_activity
        
        :param p_database: Databas instance 
        :param p_one_data: The element to be checked
        :return: True if all is correct
                False if there are duplicated elements in DB
        """
        res = False
        # checking if exist activity name
        if p_one_data and p_one_data.get('activity_name', False):
            activity_name = p_one_data['activity_name'].lower() or None
            res = p_database.check_activity(activity_name)
        return res

    @staticmethod
    def get_measures(p_database):
        """
        This method recovers all 
        
        :param p_databasem: Giving a database, this method recovers all instances of measure data
        :return: A list of measures
        """

        list_of_measures = p_database.get_measures()
        return list_of_measures

    @staticmethod
    def get_user_roles(p_database):
        """
        This method recovers database user roles to help in the JSON schema check structure 
        
        
        :param p_database: The database connector 
        :return: A list of different roles in the system
        """
        list_of_roles = p_database.get_users_roles()
        return list_of_roles


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
