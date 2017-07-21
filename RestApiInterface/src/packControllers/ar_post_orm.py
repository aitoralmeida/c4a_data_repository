# -*- coding: utf-8 -*-

"""

This is the Activity Recognition controller class. It handles request from the API class to build the needed
calls into the AR database. This class is directly inherited from PostORM superclass.

"""

import datetime
import logging
import arrow
import inspect
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
    def __init__(self, autoflush=True):
        # Using AR tables instance
        PostORM.__init__(self, ar_tables, autoflush)

    def create_tables(self):
        """
        Create database tables
        :return:
        """
        return ar_tables.create_tables(self.engine)

    ###################################################################################################
    ###################################################################################################
    ######                              DATABASE VERIFIERS
    ###################################################################################################
    ###################################################################################################

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
            res = self.query(ar_tables.UserInSystem, {'username': p_username})
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
            res = ar_tables.UserInSystem.verify_auth_token(token, app)
            if res and res.get('id', False):
                user_data = self.session.query(ar_tables.UserInSystem).get(res.get('id', 0))
        return user_data

    ###################################################################################################
    ###################################################################################################
    ######                              DATABASE ADDERS
    ###################################################################################################
    ###################################################################################################

    def add_eam(self, p_data):
        """
        Giving EAM information data, this method insert the needed data into DB.


        :param p_data: A list containing instances of JSON data with the needed information
        :return:  True if everything is ok
        """

        # TODO, review tables to the new version of database

        for data in p_data:
            # Getting activity id from DB
            activity = self._get_or_create(ar_tables.Activity, activity_name=data['activity_name'].lower())
            # Insert eam information
            eam = self._get_or_create(ar_tables.EAM, duration=data['duration'], activity_id=activity.id)
            # For each location
            for location in data['locations']:
                # Insert EAM location REL and locationType
                location = self._get_or_create(ar_tables.Location, location_name=location.lower())

                # # Getting the location type or creating a default one
                # location_type = self.session.query(ar_tables.LocationLocationTypeRel).filter_by(location_id=location.id)
                # if location_type.count() == 0:
                #     # Our location doesn't have any kind of location type, so we will assign one
                #     location_type = self._get_or_create(ar_tables.LocationType,
                #                                         location_type_name='eam')
                #     location_type_rel = self._get_or_create(ar_tables.LocationLocationTypeRel, location_id=location.id,
                #                                             location_type_id=location_type.id)

                # Adding the relationship to EAM
                self._get_or_create(ar_tables.EAMLocationRel, location_id=location.id, eam_id=eam.id)
            # Insert the time ranges
            for date_range in data['start']:
                # Insert the actual range
                start_range = self._get_or_create(ar_tables.StartRange,
                                                  start_hour=date_range[0],
                                                  end_hour=date_range[1])
                # Insert the m2m table
                self._get_or_create(ar_tables.EAMStartRangeRel, start_range_id=start_range.id, eam_id=eam.id)
            # Insert the action ranges
            for action in data['actions']:
                # Insert the actual action
                action = self._get_or_create(ar_tables.CDAction, action_name=action.lower())
                # Insert the m2m table
                self._get_or_create(ar_tables.EAMCDActionRel, cd_action_id=action.id, eam_id=eam.id)

        logging.info(inspect.stack()[0][3], "data entered successfully")
        return self.commit()


    ###################################################################################################
    ###################################################################################################
    ######                              DATABASE GETTERS
    ###################################################################################################
    ###################################################################################################

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

    def get_tables(self):
        """
        List current database tables in DATABASE active connection (Current installed system).
    
        :return: A list containing current tables.
        """
        m = MetaData()
        m.reflect(self.engine, schema='city4age_ar')
        return m.tables.keys()

    def get_user_pilot(self, p_user_id):
        """
        Giving a registered user id. This method returns it's Pilot name

        :param p_user_id: The user_in_system id in the system
        :return: The Pilot name of the registered user
        """
        res = None
        user_in_role = self.session.query(ar_tables.UserInRole).filter_by(user_in_system_id=p_user_id)[0].pilot_code \
                       or None
        if user_in_role is not None:
            # We obtain the role name based on FK key obtained in the above filter
            res = self.session.query(ar_tables.Pilot).get(user_in_role).pilot_name or None
        return res

    def get_user_role(self, p_user_id):
        """
        Giving user id, this method retrieves the user role in the system.

        :param p_user_id: The user_in_system id in the system
        :return: The name of the role attached to this user
        """
        res = None

        user_in_role = self.session.query(ar_tables.UserInRole).filter_by(user_in_system_id=p_user_id)[0].cd_role_id \
                       or None
        if user_in_role is not None:
            # We obtain the role name based on FK key obtained in the above filter
            res = self.session.query(ar_tables.CDRole).get(user_in_role).role_name or None
        return res

    def get_users_pilots(self):
        """
        Thi method recovers a list of different pilots from database

        :return: A list containing the different user pilots in the system
        """
        list_of_pilots = self.session.query(ar_tables.Pilot.pilot_name).all()
        # Extracted list of pilots
        pilots = []
        for pilot in list_of_pilots:
            pilots.append(pilot[0])
        return pilots

    def get_users_roles(self):
        """
        Thi method recovers a list of different roles from database
        
        :return: A list containing the different user roles in the system
        """
        list_of_roles = self.session.query(ar_tables.CDRole.role_name).all()
        # Extracted list of actions
        roles = []
        for role in list_of_roles:
            roles.append(role[0])
        return roles

    def get_action_name(self):
        """
        This method recovers all names of stored actions from database
        
        :return: A list containing the names of the CDAction table
        """

        list_of_actions = self.session.query(ar_tables.CDAction.action_name).all()
        # Extracted list of actions
        actions = []
        for action in list_of_actions:
            actions.append(action[0])
        return actions

    def get_action(self, p_start_time, p_end_time):
        """
        By giving a start and end time, this method extracts from database the stores leas and inserts in in a
        Python dict.


        :param p_start_time: The interval start date of the extraction
        :param p_end_time: The final end date of the extraction
        :return:  A list containing a Python dictionaries with the needed LEAS.
        """

        list_of_leas = list()

        # Dates are ok, we are going to extract needed LEAS from executed action table
        query = self.session.query(ar_tables.ExecutedAction).filter(
            ar_tables.ExecutedAction.execution_datetime.between(p_start_time, p_end_time))
        logging.info(inspect.stack()[0][3], "Total founded LEAS in database: ", query.count())
        for q in query:
            # Extracting the needed data and obtaining additional values
            location_name = self.session.query(ar_tables.Location).filter_by(id=q.location_id)[0].location_name
            action_name = self.session.query(ar_tables.CDAction).filter_by(id=q.location_id)[0].action_name
            lea = {
                'executed_action_id': q.id,
                'execution_datetime': q.execution_datetime,
                'location_name': location_name,
                'action_name': action_name
            }
            # Adding the dict to the final list
            list_of_leas.append(lea)
        return list_of_leas

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
        user_in_role = self.session.query(ar_tables.UserInRole).filter_by(id=p_user_id) or None
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
        user_in_role = self.session.query(ar_tables.UserInRole).filter_by(id=p_user_id) or None
        if user_in_role and user_in_role.count() == 1 and user_in_role[0].id == int(p_user_id) and \
                        user_in_role[0].pilot_code == p_pilot:
            res = True
        return res

    def check_username(self, p_username):
        """
        Giving a username. check if if exist or not in database

        :param p_username: The username in the system
        :return: True if the user exist in database
                False if the user do not exist in database
        """
        res = False
        username = self.session.query(ar_tables.UserInSystem).filter_by(username=p_username)
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
        user_in_role = self.session.query(ar_tables.UserInRole).filter_by(id=p_user_in_role)
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
        activity = self.session.query(ar_tables.Activity).filter_by(activity_name=p_activity_name)
        if activity and activity.count() == 1:
            res = True
        return res

    def check_action(self, p_action_name):
        """
        Giving the action anem, we check if it exist or not in the system.

        :param p_action_name: The name of the action
        :return: True if the action exist in database.
                False if the action doesn't exist in database
        """
        res = False
        action = self.session.query(ar_tables.CDAction).filter_by(action_name=p_action_name)
        if action and action.count() == 1:
            res = True
        return res

    def check_location(self, p_location_name):
        """
        giving the location name, we check if it exist or not in the system.

        :param p_location_name: The name of the location
        :return: True if the location exist in the system
                False if the location deesn't exist in the system
        """
        res = False
        location = self.session.query(ar_tables.Location).filter_by(location_name=p_location_name)
        if location and location.count() == 1:
            res = True
        return res
