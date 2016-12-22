# -*- coding: utf-8 -*-

"""
This file is used to connect to the database using SQL Alchemy ORM

"""

import os
import inspect
import ConfigParser
import logging
import datetime
import tables
from sqlalchemy import create_engine, desc, MetaData
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

# Definition of stakeholders
# todo maybe is very interesting to assign some "roles" in the system to have some access". convert this into a dict
stakeholders = [
    # System
    "admin",
    # Care
    "elderly_citizen",
    "informal_caregiver",
    "caregiver",
    "operator",
    "elderly_operator",
    "sheltered_managers",
    # Medical
    "general_practicioners",
    "geriatricians",
    "medical_researcher",
    # Behavioral science
    "behaviour_scienticist",
    # Health management
    "epidermiologist",
    # City services
    "social_services",
    "city_planner",
    # Community services
    "transport_manager",
    "energy_company",
    "cultural_manager",
    "fitness_manager",
    "shop_manager",
    "shop",  # banks, restaurants, book shop........
    # Business
    "market_researche",
    "app_developer",
    "sensor_designer",
    "expert_consultancie",
    "behavioral_science",
]


class PostgORM(object):
    def __init__(self):
        # Make basic connection and setup declatarive
        self.engine = create_engine(URL(**DATABASE))
        try:
            session_mark = sessionmaker(bind=self.engine)  # Bind session engine Test connection
            session = session_mark()
            if session:
                print "Connection OK"
                self.session = session
        except OperationalError:
            print "Database arguments are invalid"

    def create_tables(self):
        """
        Create database tables
        :return:
        """
        return tables.create_tables(self.engine)

    def insert_one(self, p_data):
        """
        Insert one desired data

        :param p_data: Object from Tables
        :return: None
        """
        self.session.add(p_data)  # Pending add (we can see new changes before commit)

    def insert_all(self, p_list_data):
        """
        Insert a list of Type of datas

        :param p_list_data: List of data
        :return: None
        """
        self.session.add_all(p_list_data)  # Multiple users, pending action

    def query(self, p_class, web_dict, limit=10, offset=0, order_by='asc'):
        """
        Makes a query to the desired table of databse and filter the result based on user choice.

        :param p_class:  Name of the table to query
        :param web_dict: A dict with colums and data to filter.
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
        Force close the connecion of the actual session

        :return: None
        """
        if self.session:
            self.session.close()

    def verify_user_login(self, p_data, app, expiration=600):
        """
        This method generates a new auth token to the user when username and password are OK

        :param p_data: A Python dic with username and password.
        :param app: Flask application Object.
        :param expiration: Expiration time of the token.

        :return: A string with token data or Error String.
        """
        res = False
        if 'username' in p_data and 'password' in p_data and app:
            user_data = self.query(tables.UserInSystem, {'username': p_data['username']})
            if user_data and user_data.count() == 1 and user_data[0].password == p_data['password'] \
                    and user_data[0].username == p_data['username']:
                logging.info("verify_user_login: Login ok.")
                # Generation of a new user Toke containing user ID
                res = user_data[0].generate_auth_token(app, expiration)
            else:
                logging.error("verify_user_login: User entered invalid username/password")
        else:
            logging.error("verify_user_login: Rare error detected")
        return res

    def verify_auth_token(self, token, app):
        """
        This method verify user's token

        :param token: Token information
        :param app: Flask application Object

        :return: All user data or None
        """
        user_data = None
        if app and token:
            res = tables.UserInSystem.verify_auth_token(token, app)
            if res and res.get('id', False):
                user_data = self.session.query(tables.UserInSystem).get(res.get('id', 0))
        return user_data

    def add_action(self, p_data):
        """
        Adds a new action into the database.

        This method divided all data in p_data parameter to create needed data and store it into database


        :param p_data: a Python d
        :return: True if everything is OK or False if there is a problem.
        """
        for data in p_data:
            insert_data_list = []
            # Basic tables
            # We are going to check if basic data exist in DB and insert it in case that is the first time.
            action = self._get_or_create(tables.Action, action_name=data['action'])
            executed_action_date = datetime.datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
            pilot = self._get_or_create(tables.Pilot, name=data['extra']['pilot'])
            user = self._get_or_create(tables.UserInRole, id=data['payload']['user'], pilot_name=pilot.name)
            location = self._get_or_create(tables.Location, location_name=data['location'], indoor=True,
                                           pilot_name=pilot.name)
            # We insert all related data to executed_action
            executed_action = tables.ExecutedAction(executed_action_date=executed_action_date, rating=data['rating'],
                                                    location_id=location.id,
                                                    action_id=action.id,
                                                    user_in_role_id=user.id)
            insert_data_list.append(executed_action)
            self.insert_all(insert_data_list)
        # Whe prepared all data, now we are going to commit it into DB.
        return self.commit()

    def add_activity(self, p_data):
        """
        Adds a new activity into the database by finding first if the location exists or not into DB

        :param p_data:
        :return: True if everything goes well.
                False if there are any problem

        """
        for data in p_data:
            # We are going to find if location is inside DB
            pilot = self._get_or_create(tables.Pilot, name=data['pilot'])
            location = self._get_or_create(tables.Location, location_name=data['location']['name'],
                                           indoor=data['location']['indoor'], pilot_name=pilot.name)
            # Creating new Activity.......
            activity = tables.Activity(activity_name=data['activity_name'],
                                       activity_start_date=data['activity_start_date'],
                                       activity_end_date=data['activity_end_date'],
                                       since=data['since'],
                                       house_number=data['house_number'],
                                       location_id=location.id
                                       )
            # Insert data into DB
            self.insert_one(activity)
        return self.commit()

    def add_measure(self, p_data):
        """
        Adds new measures into the database.


        :param p_data:
        :return: Tue if data is inserted into database.
                False if there is an error during operation
        """

        for data in p_data:
            # Iterate the user data to extract required information and process it
            pass

        return self.commit()

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
            self.commit()
            return instance

    # TODO this class will change with v.2 stakeholder
    def add_new_user_in_system(self, p_data):
        """
        This method, allows to administrative system users, add new user into the system.

        These administrative users need to set what is the stakeholder of the user in this system.

        If all is well, this method will return a boolean value, otherwise it will return a message containing a list of
        stakeholders, defined in a global list variable.

        :param p_data:
        :return: True if everything goes well.
                 False if there are any problem
                 A list of stakeholders if the user entered an invalid stakeholder.

        """
        res = False
        for data in p_data:
            # TODO You need to check first if ALL data is in stakeholders before doing anything.
            if data and 'type' in data and data['type'] in stakeholders:
                # StakeHolder entered ok we are going to enter data in DB
                stakeholder = self._get_or_create(tables.StakeHolder, name=data[
                    'type'])  # consider to enter a user type according to it'ts current role
                user_in_system = self._get_or_create(tables.UserInSystem, username=data['username'],
                                                     password=data['password'],
                                                     stake_holder_name=stakeholder.name)

                if stakeholder and user_in_system:
                    logging.info("Data entered ok into the system")
                    res = True
            else:
                res = stakeholders
                logging.error("There isn't a stakeholder inside JSON or data is invalid, value is: ", data['type'] or
                              None)
                break
        return res

    def clear_user_data_in_system(self, p_data):
        """
        This method allows to administrative system users, delete all user related data.

        The administrative users needs to send a list containing username and its stakeholders to
        perform a clean of their stored data.

        If the clean action is successful the system will return a True state, otherwise it will returns an False state
        and write into logging what is the error.

        :param p_data: A list containing users to be cleaned from system
        :return: True if everything goes well.
                False if there are any problem.
        """
        res = False
        for data in p_data:
            instance = self.session.query(tables.UserInRole).filter_by(id=data['id'],
                                                                       stake_holder_name=data['type']).first()
            if instance:
                self.session.delete(instance)
                res = True
            else:
                res = False
                break
        # Commit changes
        self.commit()
        return res

    def add_historical(self, p_user_id, p_route, p_ip, p_agent, p_data, p_status_code):
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
        new_historical = tables.Historical(route=p_route, data=p_data, ip=p_ip, agent=p_agent, status_code=p_status_code,
                                           user_in_system_id=p_user_id)
        self.insert_one(new_historical)
        return self.commit()

    def get_tables(self):
        """
        List current database tables in DATABASE active connection (Current installed system).

        :return: A list containing current tables.
        """
        m = MetaData()
        m.reflect(self.engine)
        return m.tables.keys()

    def get_table_object_by_name(self, p_table_name):
        """
        Using a table name, this class search an retrieves, Table Object Class.

        :param p_table_name: The named of target table
        :return:  A table class object.
        """
        all_tables = {
            'action': tables.Action,
            'activity': tables.Activity,
            'eam': tables.EAM,
            'executed_action': tables.ExecutedAction,
            'inter_behaviour': tables.InterBehaviour,
            'location': tables.Location,
            'pilot': tables.Pilot,
            'simple_location': tables.SimpleLocation,
            'stake_holder': tables.StakeHolder,
            'user_in_role': tables.UserInRole,
            'user_in_system': tables.UserInSystem
        }
        # We instantiate desired table
        return all_tables[p_table_name]

# todo for testing purposes, we need to delete later.

if __name__ == '__main__':
    orm = PostgORM()
    # Creating base tables
    orm.create_tables()
    # Adding system stakeholders
    list_of_stakeholders = []
    for stakeholder in stakeholders:
        list_of_stakeholders.append(tables.StakeHolder(name=stakeholder, type=stakeholder))
    orm.session.add_all(list_of_stakeholders)
    # Creating a simple admin user
    admin = john = tables.UserInSystem(username='admin', password='admin', stake_holder_name='admin')
    orm.session.add(admin)
    # Creating pilots names
    list_of_pilots = list()
    madrid = tables.Pilot(name='madrid', pilot_code='MAD', population_size=3141991)
    lecce = tables.Pilot(name='lecce', pilot_code='LCC', population_size=89839)
    singapore = tables.Pilot(name='singapore', pilot_code='SIN', population_size=5610000)
    montpellier = tables.Pilot(name='montpellier', pilot_code='MLP', population_size=268456)
    athens = tables.Pilot(name='athens', pilot_code='ATH', population_size=3090508)
    birmingham = tables.Pilot(name='birmingham', pilot_code='BHX',population_size=1101360)
    list_of_pilots.extend([madrid, lecce, singapore, montpellier, athens, birmingham])
    orm.session.add_all(list_of_pilots)
    orm.commit()
