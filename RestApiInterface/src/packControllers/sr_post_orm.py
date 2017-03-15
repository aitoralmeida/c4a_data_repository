# -*- coding: utf-8 -*-

"""

This is the Shared Repository controller class. It handles request from the API class to build the needed
calls into the SR database. This class is directly inherited from PostORM superclass.

"""


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
            user_registered = self._get_or_create(sr_tables.UserRegistered, username=data['username'].lower(),
                                                  password=data['password'])

            cd_role = self._get_or_create(sr_tables.CDRole, role_name=data['roletype'])

            # Check if the user was already registered in the server
            user_in_role = self._get_or_create(sr_tables.UserInRole, id=data['user'])
            if user_in_role.cd_role_id is None and user_in_role.user_registered_id is None:
                # This is a new and empty user. Insert new information
                user_in_role.cd_role_id = cd_role.id
                user_in_role.user_registered_id = user_registered.id
            else:
                # The user already exist in the system, so only it is necessary to add the login credentials
                user_in_role.user_registered_id = user_registered.id

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


###################################################################################################
###################################################################################################
######                              DATABASE CHECKERS
###################################################################################################
###################################################################################################

    def check_username(self, p_username):
        """
        Given an usernaem. check if if exist or not in database

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
        :return: True if the user has an access in the sytem
                False if the user hasn't access in the system or it isn't exist.
        """
        res = False
        user_authenthicated = self.session.query(sr_tables.UserInRole).filter_by(id=p_user_in_role)
        if user_authenthicated and user_authenthicated.count() == 1 and user_authenthicated[0].user_registered_id == p_user_in_role:
            res = True
        return res