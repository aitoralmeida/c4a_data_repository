# -*- coding: utf-8 -*-

"""

This is the Activity Recognition controller class. It handles request from the API class to build the needed
calls into the AR database. This class is directly inherited from PostORM superclass.

"""

import datetime
import logging
import arrow
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

    ###################################################################################################
    ###################################################################################################
    ######                              DATABASE ADDERS
    ###################################################################################################
    ###################################################################################################

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
            cd_action = self._get_or_create(ar_tables.CDAction, action_name=data['action'].lower())
            pilot = self._get_or_create(ar_tables.Pilot, code=data['pilot'].lower())

            # TODO maybe is interesting to obtain first if the user_in_role exist previously in DB and obtain it's role

            # Assuming the default value --> care_receiver
            cd_role = self._get_or_create(ar_tables.CDRole, role_name='care_receiver')
            user = self._get_or_create(ar_tables.UserInRole, id=int(data['user'].split(':')[-1]), pilot_code=pilot.code,
                                       cd_role_id=cd_role.id)
            # Adding the location
            location_type = self._get_or_create(ar_tables.LocationType,
                                                location_type_name=data['location'].split(':')[-2].lower())
            location = self._get_or_create(ar_tables.Location, location_name=data['location'].split(':')[-1].lower(),
                                           indoor=True,
                                           pilot_code=pilot.code)
            location_type_rel = self._get_or_create(ar_tables.LocationLocationTypeRel, location_id=location.id,
                                                    location_type_id=location_type.id)
            # Inserting the values attached with this action into database
            for key, value in data['payload'].items():
                if key not in ['user', 'instance_id']:
                    metric = self._get_or_create(ar_tables.Metric, name=key)
                    self._get_or_create(ar_tables.ActionValue, metric_id=metric.id, action_id=cd_action.id, value=value,
                                        date=data['timestamp'])
            # Insert a new executed action
            executed_action = ar_tables.ExecutedAction(executed_action_date=data['timestamp'],
                                                       instance_id=data['payload']['instance_id'],
                                                       location_id=location.id,
                                                       cd_action_id=cd_action.id,
                                                       user_in_role_id=user.id,
                                                       data_source_type=' '.join(data['extra'].get('data_source_type',
                                                                                                   ['sensors'])))
            # pending insert
            self.insert_one(executed_action)
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
            # Adding the new activity
            activity = self._get_or_create(ar_tables.Activity, activity_name=data['activity_name'].lower(),
                                           activity_description=data.get('activity_description', None))
            self.insert_one(activity)

        """
        # TODO use this pattern only if we decide to store more aditional data
        for data in p_data:
            # We are going to find if location is inside DB
            pilot = self._get_or_create(ar_tables.Pilot, code=data['pilot'].lower())
            # Adding the location
            location_type = self._get_or_create(ar_tables.LocationType,
                                                location_type_name=data['location'].split(':')[-2].lower())
            location = self._get_or_create(ar_tables.Location, location_name=data['location'].split(':')[-1].lower(),
                                           indoor=True, pilot_code=pilot.code)
            location_type_rel = self._get_or_create(ar_tables.LocationLocationTypeRel, location_id=location.id,
                                                    location_type_id=location_type.id)
            # Adding activity
            activity = self._get_or_create(ar_tables.Activity, activity_name=data['activity_name'].lower(),
                                           activity_start_date=data['activity_start_date'],
                                           activity_end_date=data['activity_end_date'],
                                           since=data['since'])

            # Adding location_activity_rel
            self._get_or_create(ar_tables.LocationActivityRel, activity_id=activity.id, location_id=location.id,
                                house_number=data['house_number'])

        """

        return self.commit()

    def add_new_user_in_system(self, p_data):

        """
        This method allow to an administrative user insert a new registerd user in the system or update the credentails
        of an already registered user_in_role in the system
        
        :param p_data The needed data to add a new user in the system
        :return A dict containing the data of the registered user
    
        """

        user_in_role_ids = {}
        for data in p_data:
            # Creating the user information in the system
            user_registered = self._get_or_create(ar_tables.UserRegistered, username=data['username'].lower(),
                                                  password=data['password'])
            # Getting the user information to know if is an update or a new user in the system
            user = data.get('user', False)
            if user:
                # We have already user information in the system, giving access to the user.
                # Obtaining the user instance in the system and giving it the access.
                user_in_role = self._get_or_create(ar_tables.UserInRole, id=int(data['user'].split(':')[-1]))
                user_in_role.user_registered_id = user_registered.id
            else:
                # The user is not registered in the system, so we need to create it
                cd_role = self._get_or_create(ar_tables.CDRole, role_name=p_data['roletype'])
                pilot = self._get_or_create(ar_tables.Pilot, code=p_data['pilot'].lower())
                user_in_role = self._get_or_create(ar_tables.UserInRole,
                                                   valid_from=p_data.get('valid_from', arrow.utcnow()),
                                                   valid_to=p_data.get('valid_to', None),
                                                   cd_role_id=cd_role.id,
                                                   user_registered_id=user_registered.id,
                                                   pilot_code=pilot.code)
                # Adding City4Age ID to the return value
                user_in_role_ids[data['username'].lower()] = user_in_role.id

        self.commit()
        return user_in_role_ids

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
            user_registered = self._get_or_create(ar_tables.UserRegistered, username=data['username'].lower(),
                                                  password=data['password'])
            # Gettig the CD role id of care_receiver
            cd_role = self._get_or_create(ar_tables.CDRole, role_name='care_receiver')
            # Obtaining Pilot ID through the Pilot credentials
            pilot_code = self._get_or_create(ar_tables.UserInRole, user_registered_id=p_user_id).pilot_code
            # Creating the user_in_role table for the new user in the system
            user_in_role = self._get_or_create(ar_tables.UserInRole,
                                               valid_from=data.get('valid_from', arrow.utcnow()),
                                               valid_to=data.get('valid_to', None),
                                               cd_role_id=cd_role.id,
                                               pilot_code=pilot_code,
                                               pilot_source_user_id=data.get('pilot_source_id', None),
                                               user_registered_id=user_registered.id)
            # Getting the new ID
            self.flush()
            # Adding City4Age ID to the return value
            user_in_role_ids[data['username'].lower()] = user_in_role.id

        # Return the dictionary containing the care_recievers IDs
        return user_in_role_ids

    def add_eam(self, p_data):
        """
        Giving EAM information data, this method insert the needed data into DB.


        :param p_data: A list containing instances of JSON data with the needed information
        :return:  True if everything is ok
        """

        for data in p_data:
            # Getting activity id from DB
            activity = self._get_or_create(ar_tables.Activity, activity_name=data['activity_name'].lower())
            # Insert eam information
            eam = self._get_or_create(ar_tables.EAM, duration=data['duration'], activity_id=activity.id)
            # For each location
            for location in data['locations']:
                # Insert EAM location REL and locationType
                location = self._get_or_create(ar_tables.Location, location_name=location.lower())
                # Getting the location type or creating a default one
                location_type = self.session.query(ar_tables.LocationLocationTypeRel).filter_by(location_id=location.id)
                if location_type.count() == 0:
                    # Our location doesn't have any kind of location type, so we will assign one
                    location_type = self._get_or_create(ar_tables.LocationType,
                                                        location_type_name='eam')
                    location_type_rel = self._get_or_create(ar_tables.LocationLocationTypeRel, location_id=location.id,
                                                            location_type_id=location_type.id)
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
                action = self._get_or_create(ar_tables.Action, action_name=action.lower())
                # Insert the m2m table
                self._get_or_create(ar_tables.EAMActionRel, action_id=action.id, eam_id=eam.id)

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

    ###################################################################################################
    ###################################################################################################
    ######                              DATABASE CHECKS
    ###################################################################################################
    ###################################################################################################

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

    def check_username(self, p_username):
        """
        Giving a username. check if if exist or not in database

        :param p_username: The username in the system
        :return: True if the user exist in database
                False if the user do not exist in database
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
        user_in_role = self.session.query(ar_tables.UserInRole).filter_by(id=p_user_in_role)
        if user_in_role and user_in_role.count() == 0 or user_in_role and user_in_role.count() == 1 and user_in_role[0] \
                .user_registered_id is not None:
            # The user doesn't exist in the system or it has already a user credentials
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
        action = self.session.query(ar_tables.Action).filter_by(action_name=p_action_name)
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
