# -*- coding: utf-8 -*-

"""

This class has all utilities of the project. The idea is to store all checkers, and some classes than can be useful.


"""

import logging
from collections import Counter
from flask import abort, session, request, jsonify
from jsonschema import validate, ValidationError, FormatChecker
from sqlalchemy_utils import functions
from src.packORM import ar_tables, sr_tables
from flask import current_app as app

__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2016, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"


class Utilities(object):
    ###################################################################################################
    ###################################################################################################
    ######                              Checker functions
    ###################################################################################################
    ###################################################################################################

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

        :param p_database: Database instance.
        :param p_data: data from the user.

        :return:  --> None: If all is OK
                  --> Message: A message containing the encountered error
        """

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
                    "pattern": "^(eu:c4a:[a-z,A-Z]{3,15}_[a-z,A-Z]{2,15}_[a-z,A-Z]{2,15}|eu:c4a:[a-z,A-Z]{3,15}_[a-z,A-Z]{2,15})$",
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
                    "maxLength": 100,
                    "pattern": "^(eu:c4a:[a-z,A-Z,0-9]{2,25}:[a-z,A-Z,0-9]{1,30}|eu:c4a:[a-z,A-Z,0-9]{2,25}:[a-z,A-Z,0-9]{1,35}:[a-z,A-Z,0-9]{1,35})$",
                },
                "position": {
                    "description": "The exact position given in Lat/Long format",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 100
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
                    "minProperties": 1,
                    "additionalProperties": True
                },
                "rating": {
                    "description": "Value defining the uncertainty of the inferred action",
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "exclusiveMinimum": False,
                    "exclusiveMaximum": False,
                    # "multipleOf": 0.01
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
                    "minProperties": 1,
                },
            },
            "required": ["action", "user", "pilot", "location", "position", "timestamp", "payload", "rating",
                         "data_source_type"],
            "additionalProperties": False,
        }

        try:
            # Creating a list of duplicated LEAS
            list_of_duplicated_leas_in_db = []
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
                        logging.error("The entered user pilot is incorrect or the user doesn't exist: %s" %
                                      data['user'])
                        raise ValidationError("The entered user pilot is incorrect or the user doesn't exist: %s" %
                                              data['user'])
                    elif not Utilities.validate_lea(p_database, data):
                        # Duplicated LEA, append to a list to return to the user
                        list_of_duplicated_leas_in_db.append(data)
                # Check if we have duplicated LEAS in DB an raise an error
                if len(list_of_duplicated_leas_in_db) > 0:
                     logging.error("The entered LEA is duplicated in database (same user doing the same "
                               "action in the same location at the same time, check the following values:\n %s)" % list_of_duplicated_leas_in_db)
                     raise ValidationError("The entered LEA is duplicated in database (same user doing the same "
                                       "action in the same location at the same time, check the following values:\n %s)" % list_of_duplicated_leas_in_db)

            else:
                raise ValidationError("The provided data it seems not to be a JSON list, please create a JSON list")

        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message
        return msg

    @staticmethod
    def check_add_activity_data(p_database, p_data):
        """
        Check if data is ok and if the not nullable values are filled.

        The user needs to send all data, if the location values are indoor it  must provide a valid house number, otherwise
        it must send a house number with zero value. The idea is to avoid nullable values in DB.

        :param p_database: Database instance
        :param p_data: User sent data

        :return: --> None: If all is OK
                  --> Message: A message containing the encountered error
        """
        msg = None
        # Defining schema to be compared with entered data
        schema = {
            "title": "Add activity schema",
            "type": "object",
            "properties": {
                "activity": {
                    "description": "The name of the current activity",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50
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
                "start_time": {
                    "description": "The start time when the activity is recorded",
                    "type": "string",
                    "format": "date-time",
                    "minLength": 3,
                    "maxLength": 45
                },
                "end_time": {
                    "description": "The end time when the activity is recorded",
                    "type": "string",
                    "format": "date-time",
                    "minLength": 3,
                    "maxLength": 45
                },
                "duration": {
                    "description": "The total duration in seconds of the performed activity",
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 99999999,
                },
                "payload": {
                    "description": "Additional values like action",
                    "type": "array",
                    "minItems": 0,
                    "maxItems": 30,
                    "uniqueItems": True,
                    "items": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "description": "the name of the action",
                                "type": "string",
                                "minLength": 3,
                                "maxLength": 50,
                                "pattern": "^(eu:c4a:[a-z,A-Z]{3,15}_[a-z,A-Z]{2,15}_[a-z,A-Z]{2,15}|eu:c4a:[a-z,A-Z]{3,15}_[a-z,A-Z]{2,15})$",
                            },
                            "location": {
                                "description": "Semantic location of the performed action",
                                "type": "string",
                                "minLength": 3,
                                "maxLength": 50,
                                "pattern": "^(eu:c4a:[a-z,A-Z,0-9]{2,25}:[a-z,A-Z,0-9]{1,30}|eu:c4a:[a-z,A-Z,0-9]{2,25}:[a-z,A-Z,0-9]{1,35}:[a-z,A-Z,0-9]{1,35})$",
                            },
                            "timestamp": {
                                "description": "The time when de action was performed",
                                "type": "string",
                                "format": "date-time",
                                "minLength": 3,
                                "maxLength": 45
                            },
                            "position": {
                                "description": "The exact position given in Lat/Long format",
                                "type": "string",
                                "minLength": 3,
                                "maxLength": 50
                            },
                        },
                        "additionalProperties": False,
                        "required": ["action", "location", "timestamp", "position"]
                    }
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
            "required": ["activity", "user", "pilot", "start_time", "end_time", "duration", "data_source_type"],
            "additionalProperties": False
        }

        try:
            # if type(p_data) is list:
            # We have a list of dicts
            # list_of_activities = []
            for data in p_data:
                validate(data, schema, format_checker=FormatChecker())
                # check if the activity exist in database or not
                if not Utilities.validate_activity(p_database, data):
                    # The activity exist already in database
                    logging.error("The entered activity doesn't exist: %s" % data['activity'])
                    raise ValidationError("The entered activity doesn't exist: %s" % data['activity'])
                # Appending the activity
                # list_of_activities.append(data['activity'])
                elif not Utilities.validate_user_pilot(p_database, data['user'].split(':')[-1].lower(), data['pilot']):
                    logging.error("The entered user doesn't exist or its Pilot is incorrect: %s -- %s" %
                                  (data['user'], data['pilot']))
                    raise ValidationError("The entered user doesn't exist or its Pilot is incorrect: %s -- %s" %
                                          (data['user'], data['pilot']))
                elif data['start_time'] > data['end_time']:
                    logging.error("Start time is greater than end time. Start_time: %s -- End_time_ %s" %
                                  (data['start_time'], data['end_time']))
                    raise ValidationError("Start time is greater than end time. Start_time: %s -- End_time_ %s" %
                                          (data['start_time'], data['end_time']))
                ###
                payload = data.get('payload', False)
                if payload:
                    # The user entered a payload of actions, we are going to check if data is consistent or not
                    for value in payload:
                        # Validating entered action
                        if not Utilities.validate_action(p_database, value):
                            logging.error("The given action in the payload doesn't exists in database: %s" % value)
                            raise ValidationError(
                                "The given action in the payload doesn't exists in database: %s" % value.get('action'))
                        elif value.get('location', False) and not Utilities.validate_location(p_database, value):
                            logging.error(
                                "The given location of the performed action doesn't exist in database: %s" % value.get(
                                    'location', False))
                            raise ValidationError("The given location of the performed action "
                                                  "doesn't exist in database: %s" % value.get('location', False))

                            # We are going to search for duplicated users in the json list sent by the user
                            # duplicated = [k for k, v in Counter(list_of_activities).items() if v > 1]
                            # if len(duplicated) > 0:
                            #    # Raise an error for duplicated values
                            #    logging.error("There are are duplicated activity names in the JSON: %s" % duplicated)
                            #    raise ValidationError("There are are duplicated activity names in the JSON: %s" % duplicated)

                            # else:
                            #     validate(p_data, schema, format_checker=FormatChecker())
                            #     # check if the activity exist in database or not
                            #     if Utilities.validate_activity(p_database, p_data):
                            #         # The activity exist already in database
                            #         logging.error("The entered activity is duplicated: %s" % p_data['activity'])
                            #         raise ValidationError("The entered activity is duplicated: %s" % p_data['activity'])
        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message
        return msg

    @staticmethod
    def check_add_new_activity_data(p_database, p_data):
        """
        Check if the given activity data is coorect and none of the sent data exists in database


        :param p_database: The database instance to call
        :param p_data: User sent data

        :return:  --> None: If all is OK
                  --> Message: A message containing the encountered error
        """
        msg = None
        schema = {
            "title": "Add new activity into the database coodebook of activities",
            "type": "object",
            "properties": {
                "activity": {
                    "description": "The name of the new activity",
                    "type": "string",
                    "minLength": 5,
                    "maxLength": 50
                },
                "description": {
                    "description": "The description of the given activity",
                    "type": "string",
                    "minLength": 5,
                    "maxLength": 200
                },
                "instrumental": {
                    "description": "Sets if the given activity is or not an instrumental activity",
                    "type": "boolean",
                },
            },
            "required": [
                "activity",
                "description",
                "instrumental"
            ],
            "additionalProperties": False
        }

        try:
            # We have a list of dicts
            list_of_activities = []
            for data in p_data:
                validate(data, schema, format_checker=FormatChecker())
                # check if the activity exist in database or not
                if Utilities.validate_activity(p_database, data):
                    # The activity exist already in database
                    logging.error("The entered activity already exists in database: %s" % data['activity'])
                    raise ValidationError("The entered activity already exists in database: %s" % data['activity'])
                # Appending the activity
                list_of_activities.append(data['activity'])
                # We are going to search for duplicated users in the json list sent by the user
                duplicated = [k for k, v in Counter(list_of_activities).items() if v > 1]
                if len(duplicated) > 0:
                    # Raise an error for duplicated values
                    logging.error("There are are duplicated activity names in the JSON: %s" % duplicated)
                    raise ValidationError("There are are duplicated activity names in the JSON: %s" % duplicated)
        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message
        return msg

    @staticmethod
    def check_add_new_user_data(p_database, p_data):
        """activity_
        Check if data is ok and if the not nullable values are filled.

        :param p_database: The database instance to call
        :param p_data: User sent data

        :return:  --> None: If all is OK
                  --> Message: A message containing the encountered error
        """

        msg = None
        schema = {
            "title": "Add new user in system schema",
            "type": "object",
            "properties": {
                "username": {
                    "description": "The username of the actual user",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50
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
                    "maxLength": 70,
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
                        logging.error("The entered username is duplicated: %s" % data['username'])
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
                    logging.error("The entered username is duplicated: %s" % p_data['username'])
                    raise ValidationError("The entered username is duplicated: %s" % p_data['username'])
                elif Utilities.validate_user_access(p_database, p_data):
                    # The user hasn't any acess in the system or there isnt any user with that ID
                    logging.error("The user entered has already a username and password " \
                                  "in the system: %s" % p_data['username'])
                    raise ValidationError("The user entered has already a username and password " \
                                          "in the system: %s" % p_data['username'])
        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message
        return msg

    @staticmethod
    def check_add_care_receiver_data(p_database, p_data):
        """
        This method checks if the entered data by a Pilot in its JSON structure is properly configured
        
    
        :param p_database: A database instance 
        :param p_data: The needed data 
        :return:  --> None: If all is OK
                  --> Message: A message containing the encountered error
        """

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
                        logging.error("The entered username is duplicated: %s" % data['username'])
                        raise ValidationError("The entered username is duplicated: %s" % data["username"])
                    # adding the username to the list
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
                    logging.error("The entered username is duplicated: %s" % p_data['username'])
                    raise ValidationError("The entered username is duplicated: %s" % p_data['username'])
        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message

        return msg

    @staticmethod
    def check_clear_user_data(p_data):
        """
        Check if data is ok

        :param p_data: User sent data

        :return:  --> None: If all is OK
                  --> Message: A message containing the encountered error
        """

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
        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message
        return msg

    @staticmethod
    def check_add_measure_data(p_database, p_data):
        """

        Check if add_measure data is entered ok with required values

        :param p_database: The database instance
        :param p_data: User data
        :return:  --> None: If all is OK
                  --> Message: A message containing the encountered error
        """

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
                        "DAY", "1WK", "2WK", "MON", "QTR", "SEM", "1YR", "2YR", "3YR", "5YR",
                        "day", "1wk", "2wk", "mon", "qtr", "sem", "1yr", "2yr", "3yr", "5yr"
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
                                    "exclusiveMinimum": False,
                                    "exclusiveMaximum": False,
                                    # "multipleOf": 0.01
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
                                "notice": {
                                    "description": "additional comments of the given measure",
                                    "type": "string",
                                    "minLength": 5,
                                    "maxLength": 2000,
                                },
                            },
                            "additionalProperties": False,
                            "required": ["value"]
                        },
                    },
                    "additionalProperties": False,
                    "minProperties": 1,
                    "maxProperties": 30
                },
                "extra": {
                    "description": "Additional information given by the Pilot in the LEA",
                    "type": "object",
                    "additionalProperties": True,
                    "minProperties": 1,
                }
            },
            "additionalProperties": False,
            "oneOf": [
                {"required": ["user", "pilot", "interval_start", "duration"]},
                {"required": ["user", "pilot", "interval_start", "interval_end"]}
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
                            logging.error("The entered measure doesn't exist: %s" % payload)
                            raise ValidationError("The entered measure doesn't exist: %s" % payload)
                    # Validating the user with its pilot
                    if not Utilities.validate_user_pilot(p_database, data['user'].split(':')[-1].lower(),
                                                         data['pilot'].lower()):
                        logging.error("The entered user pilot is incorrect or the user doesn't exist: %s" %
                                      data['user'])
                        raise ValidationError("The entered user pilot is incorrect or the user doesn't exist: %s" %
                                              data['user'])

                    # TODO validate measure

        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message
        return msg

    @staticmethod
    def check_search_data(p_ar_database, p_sr_database, p_data):
        """
        Check if search data is ok and evaluates what is the best table that fits with search criteria

        :param p_database: The database instantiation of SQL Alchemy
        :param p_data: User sent data

        :return:   --> None: If all is OK
                  --> Message: A message containing the encountered error
        """

        msg = None
        schema = {
            "title": "Search datasets schema validator",
            "type": "object",
            "properties": {
                "table": {
                    "description": "The name of the target table to make the search",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50,
                    "enum": Utilities.get_available_tables()
                },
                "criteria": {
                    "description": "The user search criteria",
                    "type": "object",
                },
                "limit": {
                    "description": "The limit of the query",
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 10000
                },
                "offset": {
                    "description": "The offset of the query",
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 1000
                },
                "order_by": {
                    "description": "The name of the target table to make the search",
                    "type": "string",
                    "maxLength": 4,
                    "enum": ['asc', 'desc']
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
                    # Validating table columns
                    ar_columns = Utilities.get_table_columns(p_ar_database, data['table'])
                    sr_columns = Utilities.get_table_columns(p_sr_database, data['table'])
                    if ar_columns and sr_columns or ar_columns and not sr_columns:
                        # Shared columns, we only check in one schema
                        for key, value in data['criteria'].items():
                            if ar_columns.get(key, None) is None:
                                logging.error(
                                    "The entered columns doesn't exist in this table. Available columns are: %s" % ar_columns.keys())
                                raise ValidationError(
                                    "The entered columns doesn't exist in this table. Available columns are: %s" % ar_columns.keys())
                    else:
                        # Only sr_columns, we check the SR schema
                        for key, value in data['criteria'].items():
                            if sr_columns.get(key, None) is None:
                                logging.error(
                                    "The entered columns doesn't exist in this table. Available columns are: %s" % sr_columns.keys())
                                raise ValidationError(
                                    "The entered columns doesn't exist in this table. Available columns are: %s" % sr_columns.keys())
                                # Once we validate that data is OK, we are going to validate database tables and columns
        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message
        return msg

    @staticmethod
    def check_add_eam_data(p_database, p_data, p_pilot_code):
        """
        This method checks if the current data is properly JSON formatted with the required files


        :param p_database: The database instance
        :param p_data: The data sent by the user

        :return:  --> None: If all is OK
                  --> Message: A message containing the encountered error
        """

        msg = None
        schema = {
            "title": "Eam database additional data validator",
            "type": "object",
            "properties": {
                # "eam": {
                #     "description": "The unique name of the EAM",
                #     "type": "string",
                #     "minLength": 3,
                #     "maxLength": 50,
                #     "pattern": "^(mad|sin|ath|bhx|lcc|mpl):[0-9]{1,20}:[a-z]{1,55}$",
                # },
                # "user": {
                #     "description": "The user in role of the EAM. Default to Pilot if not filled",
                #     "type": "string",
                #     "minLength": 3,
                #     "maxLength": 50,
                #     "pattern": "^eu:c4a:user:[0-9]{1,15}$",
                # },
                "activity": {
                    "description": "The name of the current activity",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50
                },
                "locations": {
                    "description": "A list containing the possible locations of the EAM",
                    "type": "array",
                    "items": {
                        "type": "string",
                        "pattern": "^eu:c4a:[a-z,A-Z]{2,25}$",
                    },
                    "minItems": 1,
                    "uniqueItems": True,
                    "additionalProperties": False,
                },
                "transformed_action": {
                    "description": "A list containing the transformed actions of the EAM",
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
                "activity",
                "locations",
                "transformed_action",
                "duration",
                "start"
            ],
            "additionalProperties": False
        }

        try:
            if type(p_data) is list:
                # We have a list of dicts
                list_of_eams = []
                for data in p_data:
                    validate(data, schema, format_checker=FormatChecker())
                    # Checking data integrity
                    if not Utilities.validate_transformed_action(p_database, data):
                        logging.error("The entered transformed action is not valid: %s" %
                                      data.get('transformed_action', False))
                        raise ValidationError("The entered transformed action is not valid: %s" %
                                              data.get('transformed_action', False))
                    if not Utilities.validate_activity(p_database, data):
                        logging.error("The entered activity is not valid: %s" %
                                      data.get('activity'), False)
                        raise ValidationError("The entered activity is not valid: %s" %
                                              data.get('activity'), False)
                    # if Utilities.validate_eam_name(p_database, data):
                    #     logging.error("The entered eam name is in database already: %s" %
                    #                   data.get('eam'), False)
                    #     raise ValidationError("The entered eam is in database already: %s" %
                    #                           data.get('eam'), False)
                    # if data.get('user', False):
                    #     # There is a user attached to this EAM
                    #     if not Utilities.validate_user(p_database, data):
                    #         logging.error("The entered user doesn't exist in database: %s" % data.get('user', False))
                    #         raise ValidationError("The entered user doesn't exist in database: %s" %
                    #                               data.get('user', False))
                    #     # check if the entered user is from the current Pilot
                    #     if not Utilities.validate_user_pilot(p_database, data['user'].split(':')[-1], p_pilot_code):
                    #         logging.error("The entered user isn't belongs to your Pilot: %s" % data.get('user', False))
                    #         raise ValidationError("The entered user isn't belongs to your Pilot: %s" %
                    #                               data.get('user', False))

                    # Check if locations exist previously in database
                    for location in data['locations']:
                        # We need to format the location in order to use the validator
                        a_location = {'location': location}
                        if not Utilities.validate_like_location(p_database, a_location):
                            logging.error("The entered location doesn't exist in database")
                            raise ValidationError("The entered location doesn't exsit in database: %s" %
                                                  a_location.get('location', False))
                    # After knowing that entered data is valid, we are going to check if the given eam format is
                    # correct and it fits with the sent data
                    # eam_name = data['eam'].lower().split(':')
                    # city4age_id = data['user'].split(':')[-1]
                    # if eam_name[-2] != city4age_id or eam_name[-1].lower() != data['activity'].lower():
                    #     # The entered EAM name is not correct
                    #     logging.error(
                    #         "The entered EAM name is not correct according to the city4age id or activity name."
                    #         "The entered format should be: pilot_code:city4ageid:activity"
                    #         "\n * Entered City4AgeId: %s"
                    #         "\n * Entered Activity: %s"
                    #         "\n * Entered EAM: %s" % (data['user'].split(':')[-1], data['activity'], data['eam']))
                    #
                    #     raise ValidationError(
                    #         "The entered EAM name is not correct acording to the city4age id or activity name"
                    #         "The entered format should be: pilot_code:city4ageid:activity:"
                    #         "\n * Entered City4AgeId: %s"
                    #         "\n * Entered Activity: %s"
                    #         "\n * Entered EAM: %s" % (data['user'].split(':')[-1], data['activity'], data['eam']))
                    # EAM is valid, we append in a list to avoid duplicated entries
                    # list_of_eams.append(data['eam'])
                # Check if exist duplicated values in the provided eam list
                # duplicated = [k for k, v in Counter(list_of_eams).items() if v > 1]
                # if len(duplicated) > 0:
                # Raise an error for duplicated values
                #    logging.error("There are are duplicated eam names in the JSON: %s" % duplicated)
                #    raise ValidationError("There are are duplicated eam names in the JSON: %s" % duplicated)
        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message
        return msg

    @staticmethod
    def check_add_frailty_status(p_database, p_data, p_pilot_code):
        """
        This method checks if the given frailty_status data is correct


        :param p_database: The database instance
        :param dict p_data: The data sent by the user

        :return:  --> None: If all is OK
                  --> Message: A message containing the encountered error

        :rtype basestring or None
        """
        msg = None
        schema = {
            "title": "The frailty status condition validation",
            "type": "object",
            "properties": {
                "user": {
                    "description": "The user in role. Default to Pilot if not filled",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50,
                    "pattern": "^eu:c4a:user:[0-9]{1,15}$",
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
                        "DAY", "1WK", "2WK", "MON", "QTR", "SEM", "1YR", "2YR", "3YR", "5YR",
                        "day", "1wk", "2wk", "mon", "qtr", "sem", "1yr", "2yr", "3yr", "5yr"
                    ]
                },
                "interval_end": {
                    "description": "The end time when the measure is recorded",
                    "type": "string",
                    "format": "date-time",
                    "minLength": 3,
                    "maxLength": 45
                },
                "condition": {
                    "description": "Sets the user condition",
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 10,
                    "enum": ["frail", "pre-frail", "fit", "FRAIL", "PRE-FRAIL", "FIT"]
                },
                "notice": {
                    "description": "Description of the selected status",
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 200,

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
            "additionalProperties": False,
            "oneOf": [
                {"required": ["user", "interval_start", "condition", "notice", "duration"]},
                {"required": ["user", "interval_start", "condition", "notice", "interval_end"]}
            ]
        }

        try:
            if type(p_data) is list:
                # Initializing the list of users to avoid duplicated users
                list_of_users = []
                for data in p_data:
                    validate(data, schema, format_checker=FormatChecker())
                    # Validating the entered user
                    if not Utilities.validate_user(p_database, data):
                        logging.error("The entered user doesn't exist in database: %s" % data.get('user', False))
                        raise ValidationError("The entered user doesn't exist in database: %s" %
                                              data.get('user', False))
                    # check if the entered user is from the current Pilot
                    if not Utilities.validate_user_pilot(p_database, data['user'].split(':')[-1], p_pilot_code):
                        logging.error("The entered user isn't belongs to your Pilot: %s" % data.get('user', False))
                        raise ValidationError("The entered user isn't belongs to your Pilot: %s" %
                                              data.get('user', False))

                    # TODO control check of duplicated values --> SAME user in the SAME INTERVAL DIFFERENT FRAILT STATUS

                    # If data is valid we add the current user
                    list_of_users.append(data['user'])
                # Once finished, we check for duplicated users
                duplicated = [k for k, v in Counter(list_of_users).items() if v > 1]
                if len(duplicated) > 0:
                    # Raise an error for duplicated values
                    logging.error("There are are duplicated users in the JSON: %s" % duplicated)
                    raise ValidationError("There are are duplicated users in the JSON: %s" % duplicated)
        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message
        return msg

    @staticmethod
    def check_add_factor(self, p_database, p_data):
        """
        This method check if the gven data in the addd_factor_method is consistent

        :param p_database: The database instance
        :param dict p_data: The data sent by the user

        :return:  --> None: If all is OK
                  --> Message: A message containing the encountered error

        :rtype basestring or None

        """

        msg = None
        schema = {
            "title": "The frailty status condition validation",
            "type": "object",
            "properties": {
                "user": {
                    "description": "The user in role of the EAM. Default to Pilot if not filled",
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
                        "DAY", "1WK", "2WK", "MON", "QTR", "SEM", "1YR", "2YR", "3YR", "5YR",
                        "day", "1wk", "2wk", "mon", "qtr", "sem", "1yr", "2yr", "3yr", "5yr"
                    ]
                },
                "interval_end": {
                    "description": "The end time when the measure is recorded",
                    "type": "string",
                    "format": "date-time",
                    "minLength": 3,
                    "maxLength": 45
                },
                "factor": {
                    "description": "Identifier of the geriatric factor or sub-factor to which the assessment refers",
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 10,
                    "enum": [
                        "walking", "climbing_stairs", "still_Moving", "moving_across_rooms", "gait_balance",
                        "physical_activity",
                        "bathing_and_showering", "dressing", "self_feeding", "personal_hygiene_and_grooming",
                        "toilet_hygiene",
                        "going_out", "ability_to_cook_food", "housekeeping", "laundry", "phone_usage",
                        "new_media_communication",
                        "shopping", "transportation", "finance_management", "medication", "visits",
                        "attending_senior_centers",
                        "attending_other_social_places", "restaurant", "visit_entertainment_culture_places",
                        "watching_TV",
                        "reading_newspapers", "reading_books", "quality_of_housing", "quality_of_neighbourhood",
                        "dependence",
                        "falls", "weight", "weakness", "exhaustion", "pain", "appetite", "quality_of_sleep",
                        "visit_to_doctors",
                        "visit_to_health_related_places", "abstraction", "attention", "memory", "mood"
                    ]
                },
                "score": {
                    "description": "Score assessing the Care Receiver’s geriatric factor, as determined by Pilot’s "
                                   "geriatric staff, according to commonly accepted standards.",
                    "type": "number",
                    "minimum": 1,
                    "maximum": 5,
                    "exclusiveMinimum": False,
                    "exclusiveMaximum": False,
                },
                "notice": {
                    "description": "Description of the selected status",
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 200,

                },
            },
            "additionalProperties": False,
            "oneOf": [
                {
                    "required": [
                        "user",
                        "pilot",
                        "interval_start",
                        "duration",
                        "factor",
                        "score",
                        "notice",
                    ]
                },
                {
                    "required": [
                        "user",
                        "pilot",
                        "interval_start",
                        "interval_end",
                        "factor",
                        "score",
                        "notice"
                    ]
                }
            ]
        }

        try:
            if type(p_data) is list:
                # Initializing the list of users to avoid duplicated users
                list_of_factor = []
                for data in p_data:
                    validate(data, schema, format_checker=FormatChecker())
                    # Check if the user exist in the system
                    if not Utilities.validate_user(p_database, data):
                        logging.error("The entered user doesn't exist in database: %s" % data.get('user', False))
                        raise ValidationError("The entered user doesn't exist in database: %s" %
                                              data.get('user', False))
                    # check if the entered user is from the current Pilot
                    if not Utilities.validate_user_pilot(p_database, data['user'].split(':')[-1], data['pilot']):
                        logging.error("The entered user isn't belongs to your Pilot: %s" % data.get('user', False))
                        raise ValidationError("The entered user isn't belongs to your Pilot: %s" %
                                              data.get('user', False))

                    # IF the given data is ok, add it to the list
                    list_of_factor.append(data['user'])
                # Once finished, we check for duplicated users
                duplicated = [k for k, v in Counter(list_of_factor).items() if v > 1]
                if len(duplicated) > 0:
                    # Raise an error for duplicated values
                    logging.error("There are are duplicated users in the JSON: %s" % duplicated)
                    raise ValidationError("There are are duplicated users in the JSON: %s" % duplicated)
        except ValidationError as e:
            logging.error("The schema entered by the user is invalid")
            msg = e.message
        return msg

    ###################################################################################################
    ############################################Utilities#######################################################
    ######                              Validation functions
    ###################################################################################################
    ###################################################################################################

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
            if [s for s in current_tables if table in s]:
                res = True
        return res

    # TODO some of this methods are repetet. check to unify it
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
    def validate_user(p_database, p_one_data):
        """
        This method checks if there is already a user in the system or not

        :param p_database: The database instance
        :param p_one_data: The element to be checked

        :return: True if the user exists in the system
                False if the user doesn't exist
        """
        res = False
        if p_one_data and p_one_data.get('user', False):
            user_in_role = p_one_data['user'].lower() or None  # lowering string cases
            # Converting the user data to get the ID
            user_in_role_id = int(user_in_role.split(':')[-1])
            # Get current registered users
            res = p_database.check_user_in_role(user_in_role_id)
        return res

    @staticmethod
    def validate_user_pilot(p_database, p_user, p_pilot):
        """
        Giving a User and Pilot, this method checks if the users exist in database and if exist, it checks its pilot
        code
                
        :param p_database: The database instance 
        :param p_user: The user in the system
        :param p_pilot: The pilot 
        :return:    False: If the user doesn't exist in the system or its pilots is incorrect
                    True: If the Pilot and user fits in DB
        """

        return p_database.check_user_pilot(p_user, p_pilot.lower())

    @staticmethod
    def validate_action(p_database, p_one_data):
        """
        Giving a user action, this method check if the action of a user exist in database or not

        :param p_database: The database instance
        :param p_one_data: An action
        :return:  False: If the action doesn't exist in the system
                  True: If the action exist in the system
        """
        res = False
        if p_one_data and p_one_data.get('action', False):
            action = p_one_data['action'].split(':')[-1].lower() or None  # lowering string cases
            # Get current registered users
            res = p_database.check_action(action)
        return res

    @staticmethod
    def validate_lea(p_database, p_one_data):
        """
        Giving a valid LEA (add_action data) check if it exist previously in database or not

        To know if a LEA exist previously in database we need to check if a LEA contains:

            * Same LEA execution datetime from the same user in role doing the same action in the same location

            -->  (execution_datetime, user_in_role_id, cd_action_id, location_id)


        :return:
        """
        res = False
        if p_one_data and p_one_data.get('action', False) and p_one_data.get('location', False) and \
                p_one_data.get('timestamp', False) and p_one_data.get('user', False):
            # Getting the needed data
            execution_datetime = p_one_data['timestamp']
            user_in_role_id = int(p_one_data['user'].split(':')[-1].lower())    # Convert to int value
            cd_action_name = p_one_data['action'].split(':')[-1].lower()
            location_name = p_one_data['location'].lower()
            # Calling to the database to test
            res = p_database.check_lea(execution_datetime, user_in_role_id, cd_action_name, location_name)
        return res

    @staticmethod
    def validate_activity(p_database, p_one_data):
        """
        This method check in database if the current activity exist already or not to avoid
        duplicate insertion from methods like add_activity
        
        :param p_database: Databas instance 
        :param p_one_data: The element to be checked
        :return: True if the activity already exists ind database
                 False if the activity doesn't exist in database
        """
        res = False
        # checking if exist activity name
        if p_one_data and p_one_data.get('activity', False):
            activity = p_one_data['activity'].lower() or None
            res = p_database.check_activity(activity)
        return res

    @staticmethod
    def validate_transformed_action(p_database, p_one_data):
        """
        This method check in database if the current transformed action exist already or not

        :param p_database: Database instance
        :param p_one_data: The element to be checked

        :return: True if al is correct
                False if there are duplicated elements in DB
        """
        res = False
        # Checking if exists transformed action
        if p_one_data and p_one_data.get('transformed_action', False):
            transformed_action = p_one_data.get('transformed_action', False)
            for t_action in transformed_action:
                res = p_database.check_transformed_action(t_action.lower())
                if not res:
                    # One of the transformed actions doesn't exist in database
                    break
        return res

    @staticmethod
    def validate_location(p_database, p_one_data):
        """
        This method check in database if the current location exist already or not

        :param p_database: Database instance
        :param p_one_data: The element to be checked
        :return:
        """
        res = False
        if p_one_data and p_one_data.get('location', False):
            location = p_one_data['location'].lower() or None
            res = p_database.check_location(location)
        return res

    @staticmethod
    def validate_like_location(p_database, p_one_data):
        """
        This method checks if the database contains a location LIKE the given one, it only returns
        a True o False confirmation.

        This methodd has been developed taking into account the EAM class

        :param p_database: Database instance
        :param p_one_data: The element to be checked
        :return:
        """
        res = False
        if p_one_data and p_one_data.get('location', False):
            location = p_one_data['location'].lower() or None
            res = p_database.check_like_location(location)
        return res

    @staticmethod
    def validate_eam_name(p_database, p_one_data):
        """
        This method checks if the given eam name exits previously in database

        :param p_database: Database instance
        :param p_one_data: The element to be checked
        :return: True if validation is  OK
                False if validation is KO
        """
        res = False
        if p_one_data and p_one_data.get('eam', False):
            eam = p_one_data['eam'].lower() or None
            res = p_database.check_eam(eam)
        return res

    @staticmethod
    def get_measures(p_database):
        """
        This method recovers all 
        
        :param p_database: Giving a database, this method recovers all instances of measure data
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
    def get_available_tables():
        """
        This method contains a simple list to know what are the available tables used in the search endpoint

        :return:
        """
        available_tables = ['executed_action', 'cd_action', 'cd_activity', 'executed_activity',
                            'variation_measure_value']
        return available_tables

    ###################################################################################################
    ###################################################################################################
    ######                              Universal get functions
    ###################################################################################################
    ###################################################################################################

    @staticmethod
    def get_table_by_name(p_database, p_table):
        """
        By giving the database instance and the name of the table this method returns the table instance

        :param p_database: The database instance
        :param p_table: The name of the table
        :return:
        """
        res = None
        if isinstance(p_table, str) or isinstance(p_table, unicode):
            if p_database.__class__.__name__ == 'ARPostORM':
                # Obtaining the table instance by name
                for c in ar_tables.Base._decl_class_registry.values():
                    if hasattr(c, '__tablename__') and c.__tablename__ == p_table:
                        res = c
                        break
            else:
                for c in sr_tables.Base._decl_class_registry.values():
                    if hasattr(c, '__tablename__') and c.__tablename__ == p_table:
                        res = c
                        break
        return res

    @staticmethod
    def get_table_columns(p_database, p_table):
        """
        By giving a table, obtain the columns of this table


        :param p_database The database instance
        :param p_table The name of the table
        :return: The columns of the given table or none if nothing is founded
        """
        res = None
        if isinstance(p_table, str) or isinstance(p_table, unicode):
            res = Utilities.get_table_by_name(p_database, p_table)
            if res:
                # We found the table, obtain its columns.
                res = res.__table__.columns
        return res
