# -*- coding: utf-8 -*-

"""

This is the Shared Repository controller class. It handles request from the API class to build the needed
calls into the SR database. This class is directly inherited from PostORM superclass.

"""

import arrow

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


###################################################################################################
###################################################################################################
######                              DATABASE ADDERS
###################################################################################################
###################################################################################################

    def add_measure(self, p_data):
        """
        Adds a new measure into database according to the University of Salento guidelines.

        :return:
        """

        # TODO You need to perform changes in this class and attach the data_source_type as 'sensors' for default value


        res = False

        for data in p_data:
            try:
                # Registering GEF value if it is not in DB
                gef_cd_detection_variable = self._get_or_create(sr_tables.CDDetectionVariable,
                                                                detection_variable_name=data['gef'],
                                                                detection_variable_type='gef')

                self._get_or_create(sr_tables.CDPilotDetectionVariable, pilot_name=data['extra']['pilot'],
                                    detection_variable_id=gef_cd_detection_variable.id)

                # Creating the sub-factor and attach it to GEF
                ges_cd_detection_variable = self._get_or_create(sr_tables.CDDetectionVariable,
                                                                detection_variable_name=data['ges'],
                                                                detection_variable_type='ges',
                                                                derived_detection_variable_id=gef_cd_detection_variable.id)

                # Registering the pilot to GES
                self._get_or_create(sr_tables.CDPilotDetectionVariable, pilot_name=data['extra']['pilot'],
                                    detection_variable_id=ges_cd_detection_variable.id)

                # Adding the user information
                user_in_role = self._get_or_create(sr_tables.UserInRole, id=data['payload']['user'],
                                                   pilot_name=data['extra']['pilot'])
                # Adding time interval information
                time_interval = self._get_or_create(sr_tables.TimeInterval, interval_start=data['payload']['date'])


                # Adding measure values
                for key, value in data['payload'].items():
                    if key not in ['user', 'date']:
                        # We are filtering user an data. Adding values.....
                        # Adding measure information in detection variable.
                        measure_cd_detection_variable = self._get_or_create(sr_tables.CDDetectionVariable,
                                                                            detection_variable_name=key,
                                                                            detection_variable_type='mea',
                                                                            derived_detection_variable_id=ges_cd_detection_variable.id)
                                                                            # TODO we need to put as derived from GES?

                        # Addmin measures values
                        self._get_or_create(sr_tables.VariationMeasureValue, user_in_role_id=user_in_role.id,
                                            measure_value=value, measure_type_id=measure_cd_detection_variable.id,
                                            time_interval_id=time_interval.id)

                        # OPTIONALLY adding pilot data
                        self._get_or_create(sr_tables.CDPilotDetectionVariable, pilot_name=data['extra']['pilot'],
                                            detection_variable_id=measure_cd_detection_variable.id)

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
        This method allow to an administrative user insert a new registerd user in the system or update the credentails
        of an already registered user_in_role in the system

        :param p_data The needed data to add a new user in the system
        :return A dict containing the data of the registered user

        """

        user_in_role_ids = {}
        for data in p_data:
            # Creating the user information in the system
            user_registered = self._get_or_create(sr_tables.UserRegistered, username=data['username'].lower(),
                                                  password=data['password'])
            # Getting the user information to know if is an update or a new user in the system
            user = data.get('user', False)
            if user:
                # We have already user information in the system, giving access to the user.
                # Obtaining the user instance in the system and giving it the access.
                user_in_role = self._get_or_create(sr_tables.UserInRole, id=int(data['user'].split(':')[-1]))
                user_in_role.user_registered_id = user_registered.id
            else:
                # The user is not registered in the system, so we need to create it
                cd_role = self._get_or_create(sr_tables.CDRole, role_name=p_data['roletype'])
                pilot = self._get_or_create(sr_tables.Pilot, pilot_code=p_data['pilot'])
                user_in_role = self._get_or_create(sr_tables.UserInRole,
                                                   valid_from=p_data.get('valid_from', arrow.utcnow()),
                                                   valid_to=p_data.get('valid_to', None),
                                                   cd_role_id=cd_role.id,
                                                   user_registered_id=user_registered.id,
                                                   pilot_id=pilot.id)
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
            user_registered = self._get_or_create(sr_tables.UserRegistered, username=data['username'].lower(),
                                                  password=data['password'])
            # Gettig the CD role id of care_receiver
            cd_role = self._get_or_create(sr_tables.CDRole, role_name='care_receiver')
            # Obtaining Pilot ID through the Pilot credentials
            pilot_name = self._get_or_create(sr_tables.UserInRole, user_registered_id=p_user_id).pilot_name
            # Creating the user_in_role table for the new user in the system
            user_in_role = self._get_or_create(sr_tables.UserInRole,
                                               valid_from=data.get('valid_from', arrow.utcnow()),
                                               valid_to=data.get('valid_to', None),
                                               cd_role_id=cd_role.id,
                                               pilot_name=pilot_name,
                                               pilot_source_user_id=data.get('pilot_source_id', None),
                                               user_registered_id=user_registered.id)
            # Getting the new ID
            self.flush()
            # Adding City4Age ID to the return value
            user_in_role_ids[data['username'].lower()] = user_in_role.id

        # Return the dictionary containing the care_recievers IDs
        return user_in_role_ids



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
        username = self.session.query(sr_tables.UserRegistered).filter_by(username=p_username)
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
        user_in_role = self.session.query(sr_tables.UserInRole).filter_by(id=p_user_in_role)
        if user_in_role and user_in_role.count() == 0 or user_in_role and user_in_role.count() == 1 and user_in_role[0] \
                .user_registered_id is not None:
            # The user doesn't exist in the system or it has already a user credentials
            res = True
        return res
