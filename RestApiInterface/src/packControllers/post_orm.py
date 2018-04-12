# -*- coding: utf-8 -*-

"""

The main controller class of the REST API. This class contains the common actions to manage general request
from the API.

"""

from __future__ import print_function

import os
import inspect
import ConfigParser
import logging
import arrow
from sqlalchemy import create_engine, desc, orm, cast, MetaData, String
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import OperationalError, IntegrityError
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound
# from sqlalchemy_searchable import search
from whooshalchemy import IndexService

__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2016, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"

# Database settings
config = ConfigParser.ConfigParser()
# Checks actual path of the file and sets config file.
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
config_dir = os.path.abspath(current_dir + '../../../conf/rest_api.cfg')
config.read(config_dir)

if 'database' in config.sections():
    # We have config file with data
    DATABASE = {
        'drivername': config.get('database', 'drivername') or 'postgres',
        'host': config.get('database', 'host') or 'localhost',
        'port': config.get('database', 'port') or '5432',
        'username': config.get('database', 'username') or 'postgres',
        'password': config.get('database', 'password') or 'postgres',
        'database': config.get('database', 'database') or 'postgres'
    }
else:
    # Any config file detected, load default settings.
    DATABASE = {
        'drivername': 'postgres',
        'host': 'localhost',
        'port': '5432',
        'username': 'postgres',
        'password': 'postgres',
        'database': 'postgres'
    }

# List containing the values that are considered as OUTDOOR
OUTDOOR_VALUES = ['outdoor', 'publicpark', 'cityzone', 'foodcourt', 'transportationmean', 'publictransportationmean',
                  'privatetransportationmean', 'bus', 'car', 'taxi', 'train']


class PostORM(object):
    def __init__(self, p_tables, autoflush=True):
        # Database tables schema
        self.tables = p_tables
        # Make basic connection and setup declarative
        self.engine = create_engine(URL(**DATABASE))
        orm.configure_mappers()  # Important for full text search index
        try:
            session_mark = scoped_session(sessionmaker(autoflush=autoflush, bind=self.engine))
            session = session_mark()
            if session:
                print("Database connection OK")
                logging.debug(inspect.stack()[0][3], "Database session opened successfully")
                self.session = session
                # Registering the index service
                # self._index_tables()
            else:
                print("Failed to open a database session")
                logging.error(inspect.stack()[0][3], "Failed to open database session")
                raise Exception("Failed to open database session")
        except OperationalError:
            print("Database arguments are invalid")

    ###################################################################################################
    ###################################################################################################
    ######                              SQL basic methods
    ###################################################################################################
    ###################################################################################################

    def flush(self):
        """
        Force flush the actual session. Useful for non autoflush created sessions

        :return: None
        """
        self.session.flush()

    def refresh(self, p_data):
        """
        Force refresh to pending data to obtain i'ts direct ID
        
        :param p_data: 
        :return: The updated data
        """
        self.session.refresh(p_data)

    def insert_one(self, p_data):
        """
        Insert one desired data

        :param p_data: Object from Tables
        :return: None
        """
        self.session.add(p_data)

    def insert_all(self, p_list_data):
        """
        Insert a list of Type of datas

        :param p_list_data: List of data
        :return: None
        """
        self.session.add_all(p_list_data)  # Multiple users, pending action

    def count(self, p_table):
        """
        Counts the total row of a defined table in database

        :return: The number of elements of a table
        """
        # number_elements = self.session.

    def query(self, p_class, web_dict, limit=10, offset=0, order_by='asc'):
        """
        Makes a query to the desired table of database and filter the result based on user choice.

        :param p_class:  Name of the table to query
        :param web_dict: A dict with columns and data to filter.
        :param limit: query limit (default is 10)
        :param offset: offset (default is 0)
        :param order_by: Set order of query (default is 'asc' on ID column)
        :return:
        """

        # Making the first query using the class value
        q = self.session.query(p_class)
        # Determine whether the class is a Table or a Meta
        if p_class.__class__.__name__ == 'Table':
            # The class is a reflective object, using .c to obtain columns
            table_class = p_class.c
        else:
            # The class is a Meta based object. Nothing to do
            table_class = p_class
        # Filtering the web_dict
        if q and web_dict and web_dict.items():
            # Filtering elements by criteria
            for attr, value in web_dict.items():
                # Getting attribute element
                """
                try:
                    int(value)
                    # The value is an integer, we need to perform a left side casting
                    q = q.filter(cast(getattr(table_class, attr), String).like('%%%s%%' % value))
                except ValueError:
                    q = q.filter(getattr(table_class, attr).like("%%%s%%" % value))
                """
                q = q.filter(cast(getattr(table_class, attr), String).like('%%%s%%' % value))
        # ORder by
        if order_by is not 'asc':
            q = q.order_by(desc(table_class.id))
        # Limit and offset our query
        q = q.limit(limit)
        q = q.offset(offset)
        return q

    def query_get(self, p_class, p_id):
        """
        Makes a query to the desired Table of databased based on row ID

        :param p_class:  Name of the table to query
        :param p_id: id of the row
        :return: Object instance of the class or None
        """
        q = None
        res = self.session.query(p_class).get(p_id)
        if res:
            q = res
        return q

    def commit(self):
        """
        Commit all data and close the connection to DB.

        :return: True if commit is successfully done.
                 False if there are any error in db
        """
        res = False
        try:
            self.session.commit()
            # Commit successful
            logging.info("post_orm: commit successful")
            res = True
        except Exception as e:
            logging.exception("post_orm: An error happened when commit in DB: %s", e)
            self.session.rollback()
        return res

    def rollback(self):
        """
        This is a "forced" rollback when it is necessary to call rollback in a defined situation. The class makes
        a rollback in db of the current transactions to force an exception in the code

        :return: False to indicate that the current operation has failed

        :return:
        """
        try:
            self.session.rollback()
            # Rollback done
            logging.info("post_orm: a programing based rollback has been invoked")
        except Exception as e:
            logging.exception("post_orm: An error happened when rollback in DB: %s", e)
        return False

    def close(self):
        """
        Force connection back to the connection pool of Engine

        :return: None
        """
        if self.session:
            self.session.close()

    ###################################################################################################
    ###################################################################################################
    ######                              Common API methods
    ###################################################################################################
    ###################################################################################################

    def add_new_care_receiver(self, p_data, p_user_id):
        """

        This method allow to a Pilot user, adds a new care receiver in the system. With its user credentials and so on.

        :param p_data: The data containing the new care receiver information
        :param p_user_id: The Pilot registration access id
        :return: The City4Age ID value (user_in_role table ID)
        """

        user_in_role_ids = {}
        logging.info(inspect.stack()[0][3], "adding data to database")
        for data in p_data:
            # Registering the actual user in the system
            user_in_system = self._get_or_create(self.tables.UserInSystem, username=data['username'].lower(),
                                                 password=data['password'])[0]
            # Getting the CD role id of care_receiver
            cd_role = self._get_or_create(self.tables.CDRole, role_name='Care recipient')[0]
            # Obtaining Pilot ID through the Pilot credentials

            # Obtains the pilot code. If the admin user is who is entering the user, it will default to LECCE
            pilot_code = self._get_or_create(self.tables.UserInRole, user_in_system_id=p_user_id)[0].pilot_code or 'lcc'
            # Creating the user_in_role table for the new user in the system
            user_in_role = self._get_or_create(self.tables.UserInRole,
                                               valid_from=data.get('valid_from', arrow.utcnow()),
                                               valid_to=data.get('valid_to', None),
                                               cd_role_id=cd_role.id,
                                               pilot_code=pilot_code,
                                               pilot_source_user_id=data.get('pilot_user_source_id', None),
                                               user_in_system_id=user_in_system.id)[0]
            # Adding City4Age ID to the return value
            user_in_role_ids[data['username'].lower()] = user_in_role.id

        # Return the dictionary containing the care_receivers IDs
        logging.info(inspect.stack()[0][3], "data entered successfully")
        self.commit()
        return user_in_role_ids

    def add_new_user_in_system(self, p_data):

        """
        This method allow to an administrative user insert a new registered user in the system or update the credentials
        of an already registered user_in_role in the system

        :param p_data The needed data to add a new user in the system
        :return A dict containing the data of the registered user

        """

        user_in_role_ids = {}
        logging.info(inspect.stack()[0][3], "adding data to database")
        for data in p_data:
            # Creating the user information in the system
            user_in_system = self._get_or_create(self.tables.UserInSystem, username=data['username'].lower(),
                                                 password=data['password'])[0]
            # Getting the user information to know if is an update or a new user in the system
            user = data.get('user', False)
            if user:
                # We have already user information in the system, giving access to the user.
                # Obtaining the user instance in the system and giving it the access.
                user_in_role = self._get_or_create(self.tables.UserInRole, id=int(data['user'].split(':')[-1]))[0]
                user_in_role.user_in_system_id = user_in_system.id
            else:
                # The user is not registered in the system, so we need to create it
                cd_role = self._get_or_create(self.tables.CDRole, role_name=data['roletype'])[0]
                pilot = self._get_or_create(self.tables.Pilot, pilot_code=data['pilot'].lower())[0]
                user_in_role = self._get_or_create(self.tables.UserInRole,
                                                   valid_from=data.get('valid_from', arrow.utcnow()),
                                                   valid_to=data.get('valid_to', None),
                                                   cd_role_id=cd_role.id,
                                                   user_in_system_id=user_in_system.id,
                                                   pilot_code=pilot.pilot_code)[0]
                # Adding City4Age ID to the return value
                user_in_role_ids[data['username'].lower()] = user_in_role.id

        # Commit changes
        logging.info(inspect.stack()[0][3], "data entered successfully")
        self.commit()
        return user_in_role_ids

    def add_user_action(self, p_user_id, p_route, p_ip, p_agent, p_data, p_status_code):
        """

        Adds a new entry in the historical database to record user action performed in the API.

        :param p_user_id: The Id of the registered user in the system
        :param p_route: The route that has been executed.
        :param p_ip: The ip of the user's machine
        :param p_agent: Information about the client (Browner, platform, operating system and so on)
        :param p_data: The JSON data sended by the user.
        :param p_status_code: If the response of the command is True (200 ok) or False (400, 401, 404, 500....)

        :return: True if data is stored in database
                False if there are some problems
        """

        logging.info(inspect.stack()[0][3], "adding data to database")
        new_user_action = self.tables.UserAction(route=p_route, data=p_data, ip=p_ip, agent=p_agent,
                                                 status_code=p_status_code,
                                                 user_in_system_id=p_user_id)
        self.insert_one(new_user_action)
        logging.info(inspect.stack()[0][3], "data entered successfully")
        return self.commit()

    def add_action(self, p_data):
        """
        Adds a new action into the database.

        This method divided all data in p_data parameter to create needed data and store it into database


        :param p_data: a Python dict of values
        :return: True if everything is OK or False if there is a problem.
        """

        logging.info(inspect.stack()[0][3], "adding data to database")
        for data in p_data:
            # Basic tables
            # We are going to check if basic data exist in DB and insert it in case that is the first time.
            cd_action = self._get_or_create(self.tables.CDAction, action_name=data['action'].split(':')[-1].lower())[0]
            pilot = self._get_or_create(self.tables.Pilot, pilot_code=data['pilot'].lower())[0]
            # Assuming the default value --> care_receiver
            cd_role = self._get_or_create(self.tables.CDRole, role_name='Care recipient')[0]
            user = self._get_or_create(self.tables.UserInRole, id=int(data['user'].split(':')[-1]),
                                       pilot_code=pilot.pilot_code,
                                       cd_role_id=cd_role.id)[0]
            # location_type = self._get_or_create(sr_tables.LocationType,
            #                                   location_type_name=data['location'].split(':')[-2].lower())
            # location = self._get_or_create(sr_tables.Location, location_name=data['location'].split(':')[-1].lower(),
            # Determining if the location is indoor or outdoor location
            # We asume by default that is indoor value
            indoor = True
            for value in OUTDOOR_VALUES:
                if value in data['location'].lower():
                    indoor = False
                    break
            location = self._get_or_create(self.tables.Location, location_name=data['location'].lower(),
                                           indoor=indoor,
                                           pilot_code=pilot.pilot_code)[0]
            # Insert a new executed action
            # TODO consider to update the stored data if the user send sthe same combination of user, time action and location
            """
            executed_action = self._update_or_create(self.tables.ExecutedAction,
                                                     'execution_datetime', 'cd_action_id', 'user_in_role_id',
                                                     execution_datetime=data['timestamp'],
                                                     location_id=location.id,
                                                     cd_action_id=cd_action.id,
                                                     user_in_role_id=user.id,
                                                     position=data['position'],
                                                     rating=round(data.get('rating', 0), 1),
                                                     data_source_type=' '.join(data.get('data_source_type',
                                                                                        ['sensors'])),
                                                     extra_information=' '.join(data.get('extra', None))
                                                     )
            """
            #####
            executed_action = self.tables.ExecutedAction(execution_datetime=data['timestamp'],
                                                         location_id=location.id,
                                                         cd_action_id=cd_action.id,
                                                         user_in_role_id=user.id,
                                                         position=data['position'],
                                                         rating=round(data.get('rating', 0), 1),
                                                         data_source_type=' '.join(data.get('data_source_type',
                                                                                            ['sensors'])),
                                                         )
            # Check if there are extra information and insert data
            if data.get('extra', False):
                dictlist = []
                for key, value in data.get('extra', None).items():
                    # Creating a temp list of items
                    temp = str(key) + ':' + str(value)
                    dictlist.append(temp)
                    executed_action.extra_information = ' '.join(dictlist)

            # pending insert
            self.insert_one(executed_action)
            # Generating IDS
            self.session.flush()
            # Inserting the values attached with this action into database
            list_of_payload_values = []
            for key, value in data['payload'].items():
                cd_metric = self._get_or_create(self.tables.CDMetric, metric_name=key)[0]
                if isinstance(value, list):
                    value = ' '.join(value).lower()

                # TODO consider to update the payload values

                payload_value = self.tables.PayloadValue(cd_metric_id=cd_metric.id, cd_action_id=cd_action.id,
                                                         acquisition_datetime=executed_action.acquisition_datetime,
                                                         value=str(value).lower(),
                                                         execution_datetime=data['timestamp'])
                list_of_payload_values.append(payload_value)
            # Insert all elements in pending insert
            self.insert_all(list_of_payload_values)
            # Insert transformed action elements in DB
            if self.__class__.__name__ == 'ARPostORM':
                # We are going to insert the needed transformed actions

                # TODO if the data is 'updated' we need to update the transformed action too

                res = self._add_transformed_action(data, executed_action)
                if not res:
                    log_msg = "The entered actions doesn't transformed well in add_transformed_action \n" \
                              "*action = %s \n" \
                              "location = %s \n" % (cd_action.action_name, location.location_name)
                    logging.warn(log_msg)
        logging.info(inspect.stack()[0][3], "data entered successfully")
        return self.commit()

    def add_activity(self, p_data):
        """
        Adds a new activity into the database by finding first if the location exists or not into DB

        :param p_data:
        :return: True if everything goes well.
                False if there are any problem

        """

        logging.info(inspect.stack()[0][3], "adding data to database")
        for data in p_data:
            # Getting the activity from database
            cd_activity = self.session.query(self.tables.CDActivity).filter_by(activity_name=data['activity'].lower())[
                0]
            user_in_role = self.session.query(self.tables.UserInRole).filter_by(id=int(data['user'].split(':')[-1]))[0]
            # Insert new executed activity data into DB
            executed_activity = self.tables.ExecutedActivity(start_time=data['start_time'], end_time=data['end_time'],
                                                             duration=data['duration'],
                                                             data_source_type=' '.join(data.get('data_source_type',
                                                                                                ['sensors'])),
                                                             cd_activity_id=cd_activity.id,
                                                             user_in_role_id=user_in_role.id)
            # Pending insert in database (Obtaining possible ID)
            self.insert_one(executed_activity)
            # If the entered data contains payload
            payload = data.get('payload', False)
            if payload:
                # Obtaining pilot information
                pilot = self.session.query(self.tables.Pilot).filter_by(pilot_code=data['pilot'].lower())[0]
                for value in payload:
                    # Key is the action name, Value is the needed action value to extract it from db
                    cd_action = self.session.query(self.tables.CDAction).filter_by(
                        action_name=value['action'].split(':')[-1].lower())[0]
                    location = self.session.query(self.tables.Location).filter_by(
                        location_name=value.get('location', None).lower(), pilot_code=pilot.pilot_code)[0]
                    # Obtaining executed action instance
                    executed_action = self.session.query(self.tables.ExecutedAction).filter_by(
                        user_in_role_id=user_in_role.id,
                        cd_action_id=cd_action.id,
                        location_id=location.id,
                        execution_datetime=value.get('timestamp'),
                        position=value.get('position')
                    )
                    # Once data is recovered
                    if executed_action and executed_action.count() > 0:
                        # TODO check if we recover more than one row from database
                        # Fill intermediate table between executed action and executed activity
                        executed_activity_executed_action_rel = self.tables.ExecutedActivityExecutedActionRel(
                            executed_activity_id=executed_activity.id,
                            executed_action_id=executed_action[0].id
                        )
                        # Pending insert in database
                        self.insert_one(executed_activity_executed_action_rel)
        # Commit changes
        logging.info(inspect.stack()[0][3], "data entered successfully")
        return self.commit()

    def add_new_activity(self, p_data):
        """
        Adds a new activity into the codebook database of activities.


        :param p_data: Data sent by the user
        :return: True if everything goes well.
                False if there are any problem
        """
        logging.info(inspect.stack()[0][3], "adding data to database")
        for data in p_data:
            cd_activity = self._get_or_create(self.tables.CDActivity, activity_name=data['activity'].lower(),
                                              activity_description=data['description'],
                                              instrumental=data['instrumental'])[0]
        # Commit changes9
        logging.info(inspect.stack()[0][3], "data entered successfully")
        return self.commit()

    def search(self, p_data):
        """
        By receiving a set of data. Make the needed calls inside database to extract the given search pattern

        EXAMPLE
        ========

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


        :param p_data: The search criteria data structure
        :return:  A data result based on search criteria
        """
        res = None

        # Recover each piece of data
        table = p_data.get('table', None)
        criteria = p_data.get('criteria', None)
        limit = p_data.get('limit', None)
        offset = p_data.get('offset', None)
        order_by = p_data.get('order_by', None)
        if table and criteria and len(criteria) > 0:
            # Remove some unwanted data from criteria
            if criteria.get('user_in_role_id', False):
                criteria['user_in_role_id'] = criteria['user_in_role_id'].split(':')[-1]
            if criteria.get('action', False):
                criteria['action'] = criteria['action'].split(':')[-1]
            # Obtaining the instance of table based on its name
            # Recovering the needed table instance to compute the query into database
            table_instance = self.get_table_instance(table)
            # We have needed data to make a full search
            res = self.query(table_instance, criteria, limit, offset, order_by)


            # TODO once you have the needed data, think about filtering by PILOT


        return res

        # TODO implement a full text based search
        # query = self.session.query(TABLES)
        # query = search(query, 'first')

        # query.first().name

    ###################################################################################################
    ###################################################################################################
    ######                              DATABASE CHECKS
    ###################################################################################################
    ###################################################################################################

    def check_user_in_role(self, p_user_id):
        """
        Giving user id, this method checks if the user exist or not in the system.

        :param p_user_id: The user_in_role id in the system
        :return: True if the user_in_role exist in the system
                False if it not exist in the system
        """
        res = False
        user_in_role = self.session.query(self.tables.UserInRole).filter_by(id=p_user_id) or None
        if user_in_role and user_in_role.count() == 1 and user_in_role[0].id == p_user_id:
            # The user exist in the system
            res = True
        return res

    def check_user_pilot(self, p_user_id, p_pilot):
        """
        Giving a user and a Pilot, this method checks if the user exist and if its Pilot is equal
        of the given Pilot.

        :param p_user_id: The user id of the system
        :param p_pilot: The given Pilot to compare
        :return:    False -> If the User doesn't exist in database of if the Pilot is different
                    True -> If everything is OK
        """
        res = False
        user_in_role = self.session.query(self.tables.UserInRole).filter_by(id=p_user_id) or None
        if user_in_role and user_in_role.count() == 1 and user_in_role[0].id == int(p_user_id) and \
                        user_in_role[0].pilot_code == p_pilot:
            res = True
        return res

    def check_username(self, p_username):
        """
        Given an username. check if if exist or not in database

        :param p_username: The username in the system
        :return: True if the user exist in database
                False if the user not exist in database
        """
        res = False
        username = self.session.query(self.tables.UserInSystem).filter_by(username=p_username)
        if username and username.count() == 1 and username[0].username == p_username:
            # The user exist in the system
            res = True
        return res

    def check_user_access(self, p_user_in_role):
        """
        Given a user in role, check if it has already an access in the system.

        If the user doesn't exist, we assume that it has no access in the system.

        :param p_user_in_role: The id of the user_in_role
        :return: True if the user has an access in the system
                False if the user hasn't any access in the system
        """
        res = False
        user_in_role = self.session.query(self.tables.UserInRole).filter_by(id=p_user_in_role)
        if user_in_role and user_in_role.count() == 1 and user_in_role[0].user_in_system_id is not None:
            # The user has already access in the system
            res = True
        return res

    def check_activity(self, p_activity_name):
        """
        Giving an activity name, we check if it exist or not in the system.


        :param p_activity_name: The name of an activity
        :return: True if the activity exist in the system
                False if the activity doesn't exist in the system
        """
        res = False
        activity = self.session.query(self.tables.CDActivity).filter_by(activity_name=p_activity_name)
        if activity and activity.count() == 1:
            res = True
        return res

    def check_action(self, p_action_name):
        """
        Giving the action name, we check if it exist or not in the system.

        :param p_action_name: The name of the action
        :return: True if the action exist in database.
                False if the action doesn't exist in database
        """
        res = False
        action = self.session.query(self.tables.CDAction).filter_by(action_name=p_action_name)
        if action and action.count() == 1:
            res = True
        return res

    def check_transformed_action(self, p_transformed_action_name):
        """
        Giving the transformed action name, we check if it exist or not in the system

        :param p_transformed_action_name: The name of the transformed action
        :return: True if the transformed action exist in database
                False if the action doesn't exis in database
        """
        res = False
        transformed_action = self.session.query(self.tables.CDTransformedAction). \
            filter_by(transformed_action_name=p_transformed_action_name)
        if transformed_action and transformed_action.count() == 1:
            res = True
        return res

    def check_location(self, p_location_name):
        """
        giving the location name, we check if it exist or not in the system.

        :param basestring p_location_name: The name of the location
        :return: True if the location exist in the system
                False if the location doesn't exist in the system
        :rtype: bool
        """
        res = False
        location = self.session.query(self.tables.Location).filter_by(location_name=p_location_name)
        if location and location.count() == 1:
            res = True
        return res

    def check_like_location(self, p_location_name):
        """
        giving the location name, we check if it exist or not in the system using LIKE operator

        :param  basestring p_location_name: The name of the location
        :return: True if the location exist in the system
                False if the location doesn't exist in the system
        :rtype: bool
        """
        res = False
        location = self.session.query(self.tables.Location).filter(
            self.tables.Location.location_name.like(p_location_name + '%'))
        if location.count() > 0:
            # We have data in DB
            res = True
        return res

    def check_eam(self, p_eam_name):
        """
        Giving a EAM name pattern, we check if it exist or not in the database

        :param p_eam_name: The EAM name
        :return: True if the eam exist in the system
                False if the eam doesn't exist in the system
        """
        res = False
        eam = self.session.query(self.tables.CDEAM).filter_by(eam_name=p_eam_name)
        if eam and eam.count() == 1:
            res = True
        return res

    def check_lea(self, p_execution_datetime, p_user_in_role_id, p_cd_action_name, p_location_name):
        """
        Giving a LEA basic contraint information this method ensures that a LEA is not dulicated in DB

        :param p_execution_datetime: The execution datetime of a LEA
        :param p_user_in_role_id: The City4age ID
        :param p_cd_action_name: The action name of the given LEa
        :param p_location_name: The location name of the given LEA
        :return: True if the entered data is NOT in DB
                FALSE if there is duplicated data with this samples provided
        """
        res = False
        # Obtaining location ID
        location = self.session.query(self.tables.Location).filter_by(location_name=p_location_name).first()
        if location and location.id:
            # Obtaining action ID
            cd_action = self.session.query(self.tables.CDAction).filter_by(action_name=p_cd_action_name).first()
            # Checki if the LEA exist or not
            if cd_action and location and cd_action.id and location.id:
                # Obtaining lea
                q = self.session.query(self.tables.ExecutedAction).filter_by(execution_datetime=p_execution_datetime,
                                                                             user_in_role_id=p_user_in_role_id,
                                                                             cd_action_id=cd_action.id,
                                                                             location_id=location.id)
                if q.count() == 0:
                    # There are not entries with this combination in database
                    res = True
        else:
            # If location doesn't exist yet, LEA is VALID
            res = True
        return res

    ###################################################################################################
    ###################################################################################################
    ######                              DATABASE GETTERS
    ###################################################################################################
    ###################################################################################################

    def get_tables(self, p_schema=None):
        """
        List current database tables in DATABASE active connection (Current installed system).

        :return: A list containing current tables.
        """
        m = MetaData()
        m.reflect(self.engine, schema=p_schema)
        return m.tables.keys()

    def get_table_instance(self, p_table_name, p_schema=None):
        """
        By giving a name of a table, this method returns the base instance using reflection.

        :param p_table_name The name of the table
        :param p_schema The name of the given schema

        :return: A Base instance of the table to be computed
        """
        # Reflecting data
        m = MetaData()
        m.reflect(self.engine, schema=p_schema, views=True)
        # Getting table instance
        table_instance = m.tables[p_schema + '.' + p_table_name]
        return table_instance

    def get_user_in_pilot(self, p_pilot_code):
        """
        By giving the a Pilot code we extract the total users from this Pilot

        :param p_pilot_code: The Pilot code
        :return: The City4ageId (Table ID) of the users of that Pilot if the Pilot exists
        """
        list_of_user = []
        pilot = self.session.query(self.tables.Pilot).filter_by(pilot_code=p_pilot_code)
        if pilot:
            query = self.session.query(self.tables.UserInRole).filter_by(pilot_code=p_pilot_code)
            list_of_user = [row.id for row in query.all()]

        return list_of_user


    ###################################################################################################
    ###################################################################################################
    ######                              PRIVATE METHODS
    ###################################################################################################
    ###################################################################################################

    def _get_or_create(self, model, create_method='', create_method_kwargs=None, **kwargs):
        """
        This is an advanced newly created method of get_or_create to handle asyncs when a process try to
        overlap the database inserts.

        :param model: The database table
        :param create_method: To put the classmethod decorator name to use it when creatingh the data
        :param create_method_kwargs: class method aditional args
        :param kwargs: The args of the table. Fields
        :return: Instance --> Selected or created instance
                 Boolean --> If the instance was not created it returns True, if instance is created it returns False
        """
        try:
            return self.session.query(model).filter_by(**kwargs).one(), True
        except NoResultFound:
            kwargs.update(create_method_kwargs or {})
            created = getattr(model, create_method, model)(**kwargs)
            try:
                self.session.add(created)
                self.session.flush()
                return created, False
            except IntegrityError:
                self.session.rollback()
                return self.session.query(model).filter_by(**kwargs).one(), True

    def _update_or_create(self, model, *constraint, **kwargs):
        """
        This method creates a new entry in db if this isn't exist yet or makes an update information based on some
        arguments

        :param model: The table name defined in Tables class
        :param *constraint: The name of variables to use in the constraint
        :param **kwargs: Search criteria
        :return:
        """
        # Return the constraint values from **kwargs
        search_constraint = {}
        for value in constraint:
            # Building a dict of constraints of the table
            search_constraint[value] = kwargs.get(value, None)
        # Performing the search criteria
        instance = self.session.query(model).filter_by(**search_constraint)
        if instance.count() == 1:
            # We only update data if count is == 1
            instance.update(dict(**kwargs))
            return instance.first()
        elif instance.count() == 0:
            # we don't have data, insert it
            instance = self._get_or_create(model, **kwargs)[0]
            return instance
        else:
            # This never should happen
            logging.warn('Multiple instances founded to update, skipping...')
            return None

    def _index_tables(self):
        """
        Index the needed tables according to the current session

        :return:
        """
        if self.session and self.tables and len(self.get_tables()) != 0:
            logging.debug(inspect.stack()[0][3], "Executing index service")
            # Registering index session
            index_service = IndexService(session=self.session)
            # Registering tables
            if self.__class__.__name__ == 'ARPostORM':
                # Registering AR tables
                index_service.register_class(self.tables.Location)
                index_service.register_class(self.tables.ExecutedAction)
                index_service.register_class(self.tables.ExecutedActivity)
                index_service.register_class(self.tables.PayloadValue)
                index_service.register_class(self.tables.UserInRole)
                index_service.register_class(self.tables.UserAction)
            else:
                # Registering SR tables
                index_service.register_class(self.tables.VariationMeasureValue)
                index_service.register_class(self.tables.NumericIndicatorValue)
                index_service.register_class(self.tables.GeriatricFactorValue)
                index_service.register_class(self.tables.CareProfile)
