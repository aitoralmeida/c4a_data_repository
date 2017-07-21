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
from sqlalchemy import create_engine, desc
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

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


class PostORM(object):
    def __init__(self, p_tables, autoflush=True):
        # Database tables schema
        self.tables = p_tables
        # Make basic connection and setup declarative
        self.engine = create_engine(URL(**DATABASE))
        try:
            session_mark = sessionmaker(bind=self.engine)  # Bind session engine Test connection
            session = session_mark()
            if session:
                print("Connection OK")
                if autoflush:
                    logging.info("Created session connection with autoflush")
                    self.session = session
                else:
                    logging.info("Created session connection without autoflush")
                    self.session = session.no_autoflush
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
        q = self.session.query(p_class)
        if q and web_dict and web_dict.items():
            # Filter based of the content of the dict
            for attr, value in web_dict.items():
                q = q.filter(getattr(p_class, attr).like("%%%s%%" % value))
        # ORder by
        if order_by is not 'asc':
            # Default order by id
            q = q.order_by(desc(p_class.id))
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

    def close(self):
        """
        Force close the connection of the actual session

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
        for data in p_data:
            # Registering the actual user in the system
            user_in_system = self._get_or_create(self.tables.UserInSystem, username=data['username'].lower(),
                                                 password=data['password'])
            # Gettig the CD role id of care_receiver
            cd_role = self._get_or_create(self.tables.CDRole, role_name='Care recipient')
            # Obtaining Pilot ID through the Pilot credentials
            pilot_code = self._get_or_create(self.tables.UserInRole, user_in_system_id=p_user_id).pilot_code
            # Creating the user_in_role table for the new user in the system
            user_in_role = self._get_or_create(self.tables.UserInRole,
                                               valid_from=data.get('valid_from', arrow.utcnow()),
                                               valid_to=data.get('valid_to', None),
                                               cd_role_id=cd_role.id,
                                               pilot_code=pilot_code,
                                               pilot_source_user_id=data.get('pilot_source_id', None),
                                               user_in_system_id=user_in_system.id)
            # Getting the new ID
            self.flush()
            # Adding City4Age ID to the return value
            user_in_role_ids[data['username'].lower()] = user_in_role.id

        # Return the dictionary containing the care_recievers IDs
        self.commit()
        logging.info(inspect.stack()[0][3], "data entered successfully")
        return user_in_role_ids

    def add_new_user_in_system(self, p_data):

        """
        This method allow to an administrative user insert a new registered user in the system or update the credentials
        of an already registered user_in_role in the system

        :param p_data The needed data to add a new user in the system
        :return A dict containing the data of the registered user

        """

        user_in_role_ids = {}
        for data in p_data:
            # Creating the user information in the system
            user_in_system = self._get_or_create(self.tables.UserInSystem, username=data['username'].lower(),
                                                 password=data['password'])
            # Getting the user information to know if is an update or a new user in the system
            user = data.get('user', False)
            if user:
                # We have already user information in the system, giving access to the user.
                # Obtaining the user instance in the system and giving it the access.
                user_in_role = self._get_or_create(self.tables.UserInRole, id=int(data['user'].split(':')[-1]))
                user_in_role.user_in_system_id = user_in_system.id
            else:
                # The user is not registered in the system, so we need to create it
                cd_role = self._get_or_create(self.tables.CDRole, role_name=data['roletype'])
                pilot = self._get_or_create(self.tables.Pilot, code=data['pilot'].lower())
                user_in_role = self._get_or_create(sr_tables.UserInRole,
                                                   valid_from=data.get('valid_from', arrow.utcnow()),
                                                   valid_to=data.get('valid_to', None),
                                                   cd_role_id=cd_role.id,
                                                   user_in_system_id=user_in_system.id,
                                                   pilot_code=pilot.code)
                # Adding City4Age ID to the return value
                user_in_role_ids[data['username'].lower()] = user_in_role.id

        self.commit()
        logging.info(inspect.stack()[0][3], "data entered successfully")
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


        :param p_data: a Python d
        :return: True if everything is OK or False if there is a problem.
        """

        for data in p_data:
            # Basic tables
            # We are going to check if basic data exist in DB and insert it in case that is the first time.
            cd_action = self._get_or_create(self.tables.CDAction, action_name=data['action'].split(':')[-1].lower())
            pilot = self._get_or_create(self.tables.Pilot, code=data['pilot'].lower())
            # Assuming the default value --> care_receiver
            cd_role = self._get_or_create(self.tables.CDRole, role_name='Care recipient')
            user = self._get_or_create(self.tables.UserInRole, id=int(data['user'].split(':')[-1]),
                                       pilot_code=pilot.code,
                                       cd_role_id=cd_role.id)
            # Adding the location
            # location_type = self._get_or_create(sr_tables.LocationType,
            #                                   location_type_name=data['location'].split(':')[-2].lower())
            # location = self._get_or_create(sr_tables.Location, location_name=data['location'].split(':')[-1].lower(),
            location = self._get_or_create(self.tables.Location, location_name=data['location'].lower(),
                                           indoor=True,
                                           pilot_code=pilot.code)
            # location_type_rel = self._get_or_create(sr_tables.LocationLocationTypeRel, location_id=location.id, location_type_id=location_type.id)

            # Inserting the values attached with this action into database
            for key, value in data['payload'].items():
                metric = self._get_or_create(self.tables.Metric, name=key)
                self._get_or_create(self.tables.CDActionMetric, metric_id=metric.id, cd_action_id=cd_action.id,
                                    value=value,
                                    execution_datetime=data['timestamp'])
            # Insert a new executed action
            executed_action = self.tables.ExecutedAction(execution_datetime=data['timestamp'],
                                                         location_id=location.id,
                                                         cd_action_id=cd_action.id,
                                                         user_in_role_id=user.id,
                                                         position=data['position'],
                                                         rating=round(data.get('rating', 0), 1),
                                                         data_source_type=' '.join(data.get('data_source_type',
                                                                                            ['sensors'])),
                                                         extra_information=' '.join(data.get('extra', None))
                                                         )
            # pending insert
            self.insert_one(executed_action)
        # Whe prepared all data, now we are going to commit it into DB.
        logging.info(inspect.stack()[0][3], "data entered successfully")
        return self.commit()

    def add_activity(self, p_data):
        """
        Adds a new activity into the database by finding first if the location exists or not into DB

        :param p_data:
        :return: True if everything goes well.
                False if there are any problem

        """
        for data in p_data:
            # Adding the new activity
            activity = self._get_or_create(self.tables.Activity, activity_name=data['activity_name'].lower(),
                                           activity_description=data.get('activity_description', None),
                                           instrumental=data.get('instrumental', False))
            # Optionally insert location
            if data.get('location', False) and data.get('pilot', False):
                location = self._get_or_create(self.tables.Location, location_name=data['location'].lower(),
                                               indoor=data.get('indoor', True),
                                               pilot_code=data.get('pilot', None).lower())
                # Intermediate table Location - Activity
                self._get_or_create(self.tables.LocationActivityRel, location_id=location.id, activity_id=activity.id,
                                    house_number=data.get('house_number', None))

        logging.info(inspect.stack()[0][3], "data entered successfully")
        return self.commit()

    # TODO think a method to make a query into DB and list all available tables in a desired ScHEMA.

    ########################################

    def _get_or_create(self, model, **kwargs):
        # type: (object, object) -> object
        """
        This method creates a new entry in db if this isn't exist yet or retrieve the instance information based on
        some arguments.

        :param model: The Table name defined in Tables class
        :param kwargs: The needed arguments to create the table for example

                (id=23, name='pako', lastname='rodriguez')

        :return: An instance of  the Table.
        """
        instance = self.session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance
        else:
            instance = model(**kwargs)
            self.insert_one(instance)
            # self.commit()
            return instance
