# -*- coding: utf-8 -*-

"""

This is the Shared Repository controller class. It handles request from the API class to build the needed
calls into the SR database. This class is directly inherited from PostORM superclass.

"""

import arrow
import inspect
import logging

from packORM import sr_tables
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
        # Using SR tables instance
        PostORM.__init__(self, sr_tables, autoflush)

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
        res = super(SRPostORM, self).add_user_action(p_user_id, p_route, p_ip, p_agent, p_data, p_status_code)
        return res

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
                    logging.info(inspect.stack()[0][3], ": user entered a duration")
                    time_interval = self._get_or_create(sr_tables.TimeInterval, interval_start=data['interval_start'],
                                                        typical_period=data['duration'])

                else:
                    # discrete interval
                    logging.info(inspect.stack()[0][3], ":user entered a interval end value")
                    time_interval = self._get_or_create(sr_tables.TimeInterval, interval_start=data['interval_start'],
                                                        interval_end=data['interval_end'])
                # Adding measure values
                for key, value in data['payload'].items():
                    # We are filtering user an data. Adding values.....
                    # Adding measure information in detection variable.
                    measure_cd_detection_variable = self._get_or_create(sr_tables.CDDetectionVariable,
                                                                        detection_variable_name=key.lower())
                    # Admin measures values
                    variation_measure_value = self._get_or_create(sr_tables.VariationMeasureValue,
                                                                  user_in_role_id=user_in_role.id,
                                                                  measure_value=round(value.get('value', 0), 2),
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
        logging.info(inspect.stack()[0][3], "data entered successfully")
        return res

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
        :return:    False -> If the User doesn't exist in database of if the Pilot is different
                    True -> If everything is OK
        """
        res = False
        user_in_role = self.session.query(sr_tables.UserInRole).filter_by(id=p_user_id) or None
        if user_in_role and user_in_role.count() == 1 and user_in_role[0].id == int(p_user_id) and \
                        user_in_role[0].pilot_code == p_pilot:
            res = True
        return res
