# -*- coding: utf-8 -*-

"""

This is the Shared Repository controller class. It handles request from the API class to build the needed
calls into the SR database. This class is directly inherited from PostORM superclass.

"""

import arrow
import logging

from src.packORM import sr_tables
from post_orm import PostORM
from sqlalchemy import MetaData

__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2016, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"


class SRPostORM(PostORM):
    def __init__(self, autoflush=True):
        PostORM.__init__(self, autoflush)

    def create_tables(self):
        """
        Create database tables
        :return:
        """
        return sr_tables.create_tables(self.engine)

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
        new_user_action = sr_tables.UserAction(route=p_route, data=p_data, ip=p_ip, agent=p_agent,
                                               status_code=p_status_code,
                                               user_in_system_id=p_user_id)
        self.insert_one(new_user_action)
        return self.commit()

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
            cd_action = self._get_or_create(sr_tables.CDAction, action_name=data['action'].split(':')[-1].lower())
            pilot = self._get_or_create(sr_tables.Pilot, code=data['pilot'].lower())
            # Assuming the default value --> care_receiver
            cd_role = self._get_or_create(sr_tables.CDRole, role_name='Care recipient')
            user = self._get_or_create(sr_tables.UserInRole, id=int(data['user'].split(':')[-1]), pilot_code=pilot.code,
                                       cd_role_id=cd_role.id)
            # Adding the location
            # location_type = self._get_or_create(sr_tables.LocationType,
            #                                   location_type_name=data['location'].split(':')[-2].lower())
            # location = self._get_or_create(sr_tables.Location, location_name=data['location'].split(':')[-1].lower(),
            location = self._get_or_create(sr_tables.Location, location_name=data['location'].lower(),
                                           indoor=True,
                                           pilot_code=pilot.code)
            # location_type_rel = self._get_or_create(sr_tables.LocationLocationTypeRel, location_id=location.id, location_type_id=location_type.id)

            # Inserting the values attached with this action into database
            for key, value in data['payload'].items():
                metric = self._get_or_create(sr_tables.Metric, name=key)
                self._get_or_create(sr_tables.CDActionMetric, metric_id=metric.id, cd_action_id=cd_action.id,
                                    value=value,
                                    date=data['timestamp'])
            # Insert a new executed action
            executed_action = sr_tables.ExecutedAction(execution_datetime=data['timestamp'],
                                                       location_id=location.id,
                                                       cd_action_id=cd_action.id,
                                                       user_in_role_id=user.id,
                                                       position=data['position'],
                                                       data_source_type=' '.join(data.get('data_source_type',
                                                                                          ['sensors'])),
                                                       extra_information=' '.join(data.get('extra', None))
                                                       )
            # pending insert
            self.insert_one(executed_action)
        # Whe prepared all data, now we are going to commit it into DB.
        return self.commit()

    def add_measure(self, p_data):
        """
        Adds a new measure into database according to the University of Salento guidelines.

        :return:
        """

        res = False

        for data in p_data:
            try:
                # insert pilot data
                pilot = self._get_or_create(sr_tables.Pilot, code=data['pilot'].lower())
                # Insert user in role data
                cd_role = self._get_or_create(sr_tables.CDRole, role_name='Care recipient')
                user_in_role = self._get_or_create(sr_tables.UserInRole, id=int(data['user'].split(':')[-1]),
                                                   pilot_code=pilot.code,
                                                   cd_role_id=cd_role.id)

                # Insert time interval data
                if not data.get('interval_end', False) and data.get('duration', False):
                    # nominal interval
                    # Extracting different nominal intervals
                    ar = arrow.get(data['interval_start'])
                    if data['duration'] == 'DAY':
                        # duration of 1 day
                        interval_end = ar.replace(days=1)       # Adding +1 day
                    elif data['duration'] == 'WK':
                        # duration of 7 days
                        interval_end = ar.replace(days=7)       # Adding +7 days
                    elif data['duration'] == 'MON':
                        # duration of 1 month
                        interval_end = ar.replace(months=1)     # Adding +1 month
                    else:
                        # Defaulting, maybe there is an error in the implementation
                        logging.warning("An error happened with the extraction of duration. Default to +1 day")
                        interval_end = ar.replace(days=1)
                else:
                    # Numeric interval
                    interval_end = data['interval_end']
                time_interval = self._get_or_create(sr_tables.TimeInterval, interval_start=data['interval_start'],
                                                    interval_end=interval_end)
                # Adding measure values

                for key, value in data['payload'].items():
                    # We are filtering user an data. Adding values.....
                    # Adding measure information in detection variable.
                    measure_cd_detection_variable = self._get_or_create(sr_tables.CDDetectionVariable,
                                                                        detection_variable_name=key.lower())
                    # Admin measures values
                    variation_measure_value = self._get_or_create(sr_tables.VariationMeasureValue,
                                                                  user_in_role_id=user_in_role.id,
                                                                  measure_value=value.get('value', 0),
                                                                  measure_type_id=measure_cd_detection_variable.id,
                                                                  time_interval_id=time_interval.id,
                                                                  data_source_type=' '.join(
                                                                      value.get('data_source_type', ['sensors'])))

                    # OPTIONALLY adding pilot data
                    self._get_or_create(sr_tables.CDPilotDetectionVariable, pilot_code=data['pilot'].lower(),
                                        detection_variable_id=measure_cd_detection_variable.id)

                # Check if there are extra information and insert data
                if data.get('extra', False):
                    dictlist = []
                    for key, value in data.get('extra', None).iteritems():
                        # Creating a temp list of items
                        temp = key + ':' + value
                        dictlist.append(temp)
                    variation_measure_value.extra_information = ' '.join(dictlist)
                # If all works as intended we return a true state
                res = True
            except Exception as e:
                # TODO improve this error log
                print (e)
                res = False

        # Committing and exit
        self.commit()
        return res


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
            user_in_system = self._get_or_create(sr_tables.UserInSystem, username=data['username'].lower(),
                                                 password=data['password'])
            # Getting the user information to know if is an update or a new user in the system
            user = data.get('user', False)
            if user:
                # We have already user information in the system, giving access to the user.
                # Obtaining the user instance in the system and giving it the access.
                user_in_role = self._get_or_create(sr_tables.UserInRole, id=int(data['user'].split(':')[-1]))
                user_in_role.user_in_system_id = user_in_system.id
            else:
                # The user is not registered in the system, so we need to create it
                cd_role = self._get_or_create(sr_tables.CDRole, role_name=data['roletype'])
                pilot = self._get_or_create(sr_tables.Pilot, code=data['pilot'].lower())
                user_in_role = self._get_or_create(sr_tables.UserInRole,
                                                   valid_from=data.get('valid_from', arrow.utcnow()),
                                                   valid_to=data.get('valid_to', None),
                                                   cd_role_id=cd_role.id,
                                                   user_in_system_id=user_in_system.id,
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
            user_in_system = self._get_or_create(sr_tables.UserInSystem, username=data['username'].lower(),
                                                 password=data['password'])
            # Gettig the CD role id of care_receiver
            cd_role = self._get_or_create(sr_tables.CDRole, role_name='care_receiver')
            # Obtaining Pilot ID through the Pilot credentials
            pilot_code = self._get_or_create(sr_tables.UserInRole, user_in_system_id=p_user_id).pilot_code
            # Creating the user_in_role table for the new user in the system
            user_in_role = self._get_or_create(sr_tables.UserInRole,
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
        return user_in_role_ids

    def add_activity(self, p_data):
        """
        Adds a new activity into the database by finding first if the location exists or not into DB

        :param p_data:
        :return: True if everything goes well.
                False if there are any problem

        """
        for data in p_data:
            # Adding the new activity
            activity = self._get_or_create(sr_tables.Activity, activity_name=data['activity_name'].lower(),
                                           activity_description=data.get('activity_description', None),
                                           instrumental=data.get('instrumental', False))
            # Optionally insert location
            if data.get('location', False) and data.get('pilot', False):
                location = self._get_or_create(sr_tables.Location, location_name=data['location'].lower(),
                                               indoor=data.get('indoor', True),
                                               pilot_code=data.get('pilot', None).lower())
                # Intermediate table Location - Activity
                self._get_or_create(sr_tables.LocationActivityRel, location_id=location.id, activity_id=activity.id,
                                    house_number=data.get('house_number', None))

        return self.commit()

    ###################################################################################################
    ###################################################################################################
    ######                              DATABASE GETTERS
    ###################################################################################################
    ###################################################################################################

    def get_tables(self):
        """
        List current database tables in DATABASE active connection (Current installed system).

        :return: A list containing current tables.
        """
        m = MetaData()
        m.reflect(self.engine, schema='city4age_sr')
        return m.tables.keys()

    def get_measures(self):
        """
        Retrieves a list with the names of all measures in database
        
        :return: A lis containing the measures name in database
        """
        list_measures = self.session.query(sr_tables.CDDetectionVariable.detection_variable_name).all()
        # Extracted list of actions
        measures = []
        for mea in list_measures:
            measures.append(mea[0])
        return measures

    ###################################################################################################
    ###################################################################################################
    ######                              DATABASE CHECKERS
    ###################################################################################################
    ###################################################################################################

    def check_username(self, p_username):
        """
        Given an username. check if if exist or not in database

        :param p_username: The username in the system
        :return: True if the user exist in database
                False if the user not exist in database
        """
        res = False
        username = self.session.query(sr_tables.UserInSystem).filter_by(username=p_username)
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
        user_in_role = self.session.query(sr_tables.UserInRole).filter_by(id=p_user_in_role)
        if user_in_role and user_in_role.count() == 1 and user_in_role[0].user_in_system_id is not None:
            # The user has already access in the system
            res = True
        return res

    def check_user_pilot(self, p_user_id, p_pilot):
        """
        Giving a user and a Pilot, this method checks if the user exist and if its Pilot is equal 
        of the given Pilot.

        :param p_user_id: The user id of the system 
        :param p_pilot: The given Pilot to compare
        :return: 
        """
        res = False
        user_in_role = self.session.query(sr_tables.UserInRole).filter_by(id=p_user_id) or None
        if user_in_role and user_in_role.count() == 0 or user_in_role and user_in_role.count() == 1 and \
                        user_in_role[0].id == int(p_user_id) and user_in_role[0].pilot_code == p_pilot:
            res = True
        return res