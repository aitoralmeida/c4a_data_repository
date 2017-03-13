# -*- coding: utf-8 -*-

"""

This is the Activity Recognition controller class. It handles request from the API class to build the needed
calls into the AR database. This class is directly inherited from PostORM superclass.

"""

import datetime
import logging
from sqlalchemy import MetaData
from src.packORM import ar_tables
from post_orm import PostORM

__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2016, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"


class ARPostORM(PostORM):
    def __init__(self, autoflush=True):
        PostORM.__init__(self, autoflush)

    def create_tables(self):
        """
        Create database tables
        :return:
        """
        return ar_tables.create_tables(self.engine)

    def get_auth_token(self, p_user, app, expiration=600):
        """
        Giving a registered user ID creates a new token to be authenticated

        :param p_user: The ID o a registered user
        :param app:  The Flask APP
        :param expiration:  Cookie expiration time
        :return: A token to be sent to the final user
        """
        token = None
        if p_user and app:
            # Generation of a new user Toke containing user ID
            token = p_user.generate_auth_token(app, expiration)
        return token

    def verify_user_login(self, p_username, p_password, p_app):
        """
        This methods verifies the user credentials
    
        :param p_username: The user's username
        :param p_password: The user's password
        :param p_app: Flask application Object.

    
        :return: An user information if the credentials are correct or none in other case
        """
        user_data = None
        if p_username and p_password and p_app:
            res = self.query(ar_tables.UserRegistered, {'username': p_username})
            if res and res.count() == 1 and res[0].password == p_password \
                    and res[0].username == p_username:
                logging.info("verify_user_login: Login ok.")
                user_data = res[0]
            else:
                logging.error("verify_user_login: User entered invalid username/password")
        else:
            logging.error("verify_user_login: Rare error detected")
        return user_data

    def verify_auth_token(self, token, app):
        """
        This method verify user's token
    
        :param token: Token information
        :param app: Flask application Object
    
        :return: All user data or None
        """
        user_data = None
        if app and token:
            res = ar_tables.UserRegistered.verify_auth_token(token, app)
            if res and res.get('id', False):
                user_data = self.session.query(ar_tables.UserRegistered).get(res.get('id', 0))
        return user_data

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
            action = self._get_or_create(ar_tables.Action, action_name=data['action'])
            executed_action_date = datetime.datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
            pilot = self._get_or_create(ar_tables.Pilot, name=data['extra']['pilot'])
            user = self._get_or_create(ar_tables.UserInRole, id=data['payload']['user'], pilot_name=pilot.name)
            if data.get('location', False) and isinstance(data['location'], dict):
                # The sent location is a latitude and longitude based location
                location = self._get_or_create(ar_tables.Location, latitude=data['location']['lat'],
                                               longitude=data['location']['long'], indoor=True, pilot_name=pilot.name)
            else:
                # The sent location is an URN based location
                location = self._get_or_create(ar_tables.Location, urn=data['location'], indoor=True,
                                               pilot_name=pilot.name)
            # Inserting the values attached with this action into database
            for key, value in data['payload'].items():
                if key not in ['user', 'instanceID']:
                    metric = self._get_or_create(ar_tables.Metric, name=key)
                    self._get_or_create(ar_tables.ActionValue, metric_id=metric.id, action_id=action.id, value=value,
                                        date=executed_action_date)

            # We insert all related data to executed_action
            self._get_or_create(ar_tables.ExecutedAction, executed_action_date=executed_action_date,
                                rating=data['rating'],
                                instance_id=data['payload']['instanceID'],
                                location_id=location.id,
                                action_id=action.id,
                                user_in_role_id=user.id)

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
            pilot = self._get_or_create(ar_tables.Pilot, name=data['pilot'])
            if data.get('location', False) and isinstance(data['location'], dict):
                # The sent location is a latitude and longitude based location
                location = self._get_or_create(ar_tables.Location, latitude=data['location']['lat'],
                                               longitude=data['location']['long'], indoor=data['indoor'],
                                               pilot_name=pilot.name)
            else:
                # The sent location is an URN based location
                location = self._get_or_create(ar_tables.Location, urn=data['location'], indoor=data['indoor'],
                                               pilot_name=pilot.name)

            activity = self._get_or_create(ar_tables.Activity, activity_name=data['activity_name'],
                                           activity_start_date=data['activity_start_date'],
                                           activity_end_date=data['activity_end_date'],
                                           since=data['since'])

            # Adding location_activity_rel
            self._get_or_create(ar_tables.LocationActivityRel, activity_id=activity.id, location_id=location.id,
                                house_number=data['house_number'])

        return self.commit()

    def add_new_user_in_system(self, p_data):

        """
        This method, allows to administrative system users, add new user into the system.

        The administrator MUST provide a valid user_in_role ID to grant access in the system. This function covers two
        different points:

                1.- If the user is already in the system (user_in_role) this method gives it an access to the system
                2.- If the user is not in the system, this method creates a new user accces

        :param p_data:
        :return: True if everything goes well.
                 False if there are any problem
    
        """
        for data in p_data:
            # We are going to check if the actual user exists in the system
            user_registered = self._get_or_create(ar_tables.UserRegistered, username=data['username'].lower(),
                                                  password=data['password'])

            cd_role = self._get_or_create(ar_tables.CDRole, role_name=data['roletype'])

            # Check if the user was already registered in the server
            user_in_role = self._get_or_create(ar_tables.UserInRole, id=data['user'])
            if user_in_role.cd_role_id is None and user_in_role.user_registered_id is None:
                # This is a new and empty user. Insert new information
                user_in_role.cd_role_id = cd_role.id
                user_in_role.user_registered_id = user_registered.id
            else:
                # The user already exist in the system, so only it is necessary to add the login credentials
                user_in_role.user_registered_id = user_registered.id

        return self.commit()

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
        new_user_action = ar_tables.UserAction(route=p_route, data=p_data, ip=p_ip, agent=p_agent,
                                               status_code=p_status_code,
                                               user_registered_id=p_user_id)
        self.insert_one(new_user_action)
        return self.commit()

    def get_tables(self):
        """
        List current database tables in DATABASE active connection (Current installed system).
    
        :return: A list containing current tables.
        """
        m = MetaData()
        m.reflect(self.engine, schema='city4age_ar')
        return m.tables.keys()

    def get_user_role(self, p_user_id):
        """
        Giving user id, this method retrieves the user role in the system.

        :param p_user_id: The user_registered id in the system
        :return: The name of the role attached to this user
        """
        res = None
        # TODO this method would give error if there isnt' data in database, change the logis
        user_in_role = self.session.query(ar_tables.UserInRole).filter_by(user_registered_id=p_user_id)[0].cd_role_id \
                       or None
        if user_in_role is not None:
            # We obtain the role name based on FK key obtained in the above filter
            res = self.session.query(ar_tables.CDRole).get(user_in_role).role_name or None
        return res

    def check_user_in_role(self, p_user_id):
        """
        Giving user id, this method checks if the user exist or no in the system.

        :param p_user_id: The user_in_role id in the system
        :return: True if the user_in_role exist in the system
                False if it not exist in the system
        """
        res = False
        # TODO this method would give error if there isnt' data in database, change the logis
        user_in_role = self.session.query(ar_tables.UserInRole).filter_by(id=p_user_id) or None
        if user_in_role and user_in_role.count() == 1 and user_in_role[0].id == p_user_id:
            # The user exist in the system
            res = True
        return res

    # TODO find a solution to this workaround
    def get_table_object_by_name(self, p_table_name):
        """
        Using a table name, this class search an retrieves, Table Object Class.
    
        :param p_table_name: The named of target table
        :return:  A table class object.
        """
        all_tables = {
            'action': ar_tables.Action,
            'activity': ar_tables.Activity,
            'eam': ar_tables.EAM,
            'executed_action': ar_tables.ExecutedAction,
            'inter_behaviour': ar_tables.InterBehaviour,
            'location': ar_tables.Location,
            'pilot': ar_tables.Pilot,
            'simple_location': ar_tables.SimpleLocation,
            'user_in_role': ar_tables.UserInRole,
            'user_registered': ar_tables.UserRegistered,
            'user_action': ar_tables.UserAction,
            'metric': ar_tables.Metric,
            'action_value': ar_tables.ActionValue,
        }
        # We instantiate desired table
        return all_tables[p_table_name]

    def check_username(self, p_username):
        """
        Given an usernaem. check if if exist or not in database

        :param p_username: The username in the system
        :return: True if the user exist in database
                False if the user not exist in database
        """
        res = False
        username = self.session.query(ar_tables.UserRegistered).filter_by(username=p_username)
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
                False if the user hasn't access in the system or it isn't exist.
        """
        res = False
        user_authenthicated = self.session.query(ar_tables.UserInRole).filter_by(id=p_user_in_role)
        if user_authenthicated and user_authenthicated.count() == 1 and \
                        user_authenthicated[0].user_registered_id != None:
            res = True
        return res
