# -*- coding: utf-8 -*-

"""
This file is used to connect to the database using SQL Alchemy ORM

"""

import os
import sys
import inspect
import tables
import ConfigParser
import logging
import datetime
from sqlalchemy import create_engine, desc, MetaData
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker


__author__ = 'Rubén Mulero'
__copyright__ = "foo"   # we need?¿

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
# todo maybe is very interesint to assign some "roles" in the system to have some access". convert this into a dict
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
                    "shop",     # banks, restaurants, book shop........
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
            session_mark = sessionmaker(bind=self.engine)   # Bind session engine Test connection
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
        self.session.add(p_data)                  # Pending add (we can see new changes before commit)

    def insert_all(self, p_list_data):
        """
        Insert a list of Type of datas

        :param p_list_data: List of data
        :return: None
        """
        self.session.add_all(p_list_data)         # Multiple users, pending action

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

    def query_get(self, p_class,  p_id):
        """
        Makes a querty to the desired Table of databased based on row ID

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

    def verify_user_login(self, p_data):
        """
        This method check given user and password and create a new session for the current user.

        :param p_data: User and password
        :return: True or False if user/password are valid.
        """
        res = False
        if 'username' in p_data and 'password' in p_data:
            user_data = self.query(tables.UserInSystem, {'username': p_data['username']})
            if user_data and user_data.count() == 1 and user_data[0].password == p_data['password'] \
                    and user_data[0].username == p_data['username']:
                logging.info("verify_user_login: Login ok.")
                res = user_data[0].id
            else:
                logging.error("verify_user_login: User entered invalid username/password")
        else:
            logging.error("verify_user_login: Rare error detected")
        return res


    # def verify_user_login(self, p_data, app, expiration=600):
    #     """
    #     This method generates a new auth token to the user when username and password are OK
    #
    #     :param p_data: A Python dic with username and password.
    #     :param app: Flask application Object.
    #     :param expiration: Expiration time of the token.
    #
    #     :return: A string with token data or Error String.
    #     """
    #     if 'username' in p_data and 'password' in p_data and app:
    #         user_data = self.query(tables.User, p_data)
    #         if user_data and user_data[0]:
    #             # Login OK
    #             res = user_data[0].generate_auth_token(app, expiration)
    #         else:
    #             res = "username or password incorrect"
    #     else:
    #         res = "Incorrect behaviour"
    #     return res
    #
    # def verify_auth_token(self, token, app):
    #     """
    #     This method verify user's token
    #
    #     :param token: Token information
    #     :param app: Flask application Object
    #
    #     :return: All user data or None
    #     """
    #     user_data = None
    #     if app and token:
    #         res = tables.User.verify_auth_token(token, app)
    #         if res and res.get('id', False):
    #             user_data = self.session.query(tables.User).get(res.get('id', 0))
    #     return user_data

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
            date = datetime.datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
            pilot = self._get_or_create(tables.Pilot, name=data['extra']['pilot'])
            user = self._get_or_create(tables.UserInRole, id=data['payload']['user'], pilot_name=pilot.name)
            location = self._get_or_create(tables.Location, location_name=data['location'], indoor=True,
                                           pilot_name=pilot.name)
            # We insert all related data to executed_action
            executed_action = tables.ExecutedAction(date=date, rating=data['rating'],
                                                    location_id=location.id,
                                                    action_id=action.id,
                                                    user_in_role_id=user.id)
            insert_data_list.append(executed_action)
            self.insert_all(insert_data_list)
        # Whe prepared all data, now we are going to commit it into DB.
        return self.commit()

    def add_risk(self, p_data):
        """
        Adds a new risk into the database

        This method inserts into database all information about risk and their type to be related later with desired
        data.

        :param p_data:
        :return: True if everything goes well.
                False if there are any problem

        """
        # todo this is a first version, maybe in the future the user need to specify relationships
        res = False
        for data in p_data:
            risk = self._get_or_create(tables.Risk, risk_name=data['risk_name'], ratio=data['ratio'],
                                       description=data['description'])
            if risk:
                res = True
            else:
                res = False
        return res

    def add_activity(self, p_data):
        """
        Adds a new activity into the database

        :param p_data:
        :return: True if everything goes well.
                False if there are any problem

        """
        # todo this is a first version, maybe in the future the user need to specify relationships
        res = False
        for data in p_data:
            activity = self._get_or_create(tables.Activity, activity_name=data['activity_name'])
            if activity:
                res = True
            else:
                res = False
        return res

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
                stakeholder = self._get_or_create(tables.StakeHolder, name=data['type'])    # consider to enter a user type according to it'ts current role
                user_in_system = self._get_or_create(tables.UserInSystem, username=data['username'], password=data['password'],
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

    # todo maybe we need to create stakeholders methods ???

    def get_tables(self):
        """
        List current database tables in DATABASE active connection (Current installed system).

        :return: A list containing current tables.
        """

        m = MetaData()
        m.reflect(self.engine)
        return m.tables.keys()

    def get_table_by_name(self, p_table_name):
        """
        Using a table name, this class search an retrieves, Table Object Class.

        :param p_table_name: The named of target table
        :return:  A table class object.
        """
        # Get all classes in tables
        #clsmembers = inspect.getmembers(sys.modules['src.packORM.tables'], inspect.isclass)
        # todo this is a workaround, we need to find a better solution
        # todo maybe we can obtain all tables from get_tables and filter it?¿?
        all_tables = {
                        'action': tables.Action,
                        'activity': tables.Activity,
                        'eam': tables.EAM,
                        'executed_action': tables.ExecutedAction,
                        'geriatric_indicator': tables.GeriatricIndicator,
                        'geriatric_sub_indicator': tables.GeriatricSubIndicator,
                        'inter_behaviour': tables.InterBehaviour,
                        'intra_activity': tables.IntraActivity,
                        'location': tables.Location,
                        'pilot': tables.Pilot,
                        'risk': tables.Risk,
                        'simple_location': tables.SimpleLocation,
                        'stake_holder': tables.StakeHolder,
                        'user_in_role': tables.UserInRole,
                        'user_in_system': tables.UserInSystem
                    }
        # We intantiate desired table
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
    madrid = tables.Pilot(name='madrid', population_size=3141991)
    lecce = tables.Pilot(name='lecce', population_size=89839)
    singapore = tables.Pilot(name='singapore', population_size=5610000)
    montpellier = tables.Pilot(name='montpellier', population_size=268456)
    athens = tables.Pilot(name='athens', population_size=3090508)
    birmingham = tables.Pilot(name='birmingham', population_size=1101360)
    list_of_pilots.extend([madrid, lecce, singapore, montpellier, athens, birmingham])
    orm.session.add_all(list_of_pilots)
    orm.commit()
