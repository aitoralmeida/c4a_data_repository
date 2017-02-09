# -*- coding: utf-8 -*-


import datetime
import logging
from sqlalchemy import MetaData
from packORM import ar_tables
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
    def __init__(self):
        PostORM.__init__(self)

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
            insert_data_list = []
            # Basic tables
            # We are going to check if basic data exist in DB and insert it in case that is the first time.
            action = self._get_or_create(ar_tables.Action, action_name=data['action'])
            executed_action_date = datetime.datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
            pilot = self._get_or_create(ar_tables.Pilot, name=data['extra']['pilot'])
            user = self._get_or_create(ar_tables.UserInRole, id=data['payload']['user'], pilot_name=pilot.name)
            location = self._get_or_create(ar_tables.Location, location_name=data['location'], indoor=True,
                                           pilot_name=pilot.name)
            # We insert all related data to executed_action
            executed_action = ar_tables.ExecutedAction(executed_action_date=executed_action_date,
                                                       rating=data['rating'],
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
        # TODO check when the user sen'ds a multiple locationpackORM
        res = False
        for data in p_data:
            # We are going to find if location is inside DB
            pilot = self._get_or_create(ar_tables.Pilot, name=data['pilot'])
            location = self._get_or_create(ar_tables.Location, location_name=data['location']['name'],
                                           indoor=data['location']['indoor'], pilot_name=pilot.name)

            activity = self._get_or_create(ar_tables.Activity, activity_name=data['activity_name'],
                                           activity_start_date=data['activity_start_date'],
                                           activity_end_date=data['activity_end_date'],
                                           since=data['since'])

            location_activity_rel = self._get_or_create(ar_tables.LocationActivityRel,
                                                        activity_id=activity.id,
                                                        location_id=location.id,
                                                        house_number=data['house_number'])
            # TODO check if this is a good way to check this
            if isinstance(location_activity_rel, ar_tables.LocationActivityRel):
                res = True
            else:
                res = False
                break
        return res

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


    """
    # TODO this class will change with v.2 stakeholder
    def add_new_user_in_system(self, p_data):
    
        #########################################
        This method, allows to administrative system users, add new user into the system.
    
        These administrative users need to set what is the stakeholder of the user in this system.
    
        If all is well, this method will return a boolean value, otherwise it will return a message containing a list of
        stakeholders, defined in a global list variable.
    
        :param p_data:
        :return: True if everything goes well.
                 False if there are any problem
                 A list of stakeholders if the user entered an invalid stakeholder.
    
        #######################################
    
    
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
    """

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
            instance = self.session.query(ar_tables.UserInRole).filter_by(id=data['id'],
                                                                          stake_holder_name=data[
                                                                              'type']).first()
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
        new_historical = ar_tables.Historical(route=p_route, data=p_data, ip=p_ip, agent=p_agent,
                                              status_code=p_status_code,
                                              user_registered_id=p_user_id)
        self.insert_one(new_historical)
        return self.commit()

    def get_tables(self):
        """
        List current database tables in DATABASE active connection (Current installed system).
    
        :return: A list containing current tables.
        """
        m = MetaData()
        m.reflect(self.engine, schema='city4age_ar')
        return m.tables.keys()

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
            'user_registered': ar_tables.UserRegistered
        }
        # We instantiate desired table
        return all_tables[p_table_name]
