# -*- coding: utf-8 -*-

"""

This is the Shared Repository controller class. It handles request from the API class to build the needed
calls into the SR database. This class is directly inherited from PostORM superclass.

"""

import arrow
import inspect
import logging
import subprocess

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
        # Using SR tables instance
        PostORM.__init__(self, sr_tables, autoflush)

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
        logging.info(inspect.stack()[0][3], "adding data to database")
        for data in p_data:
            try:
                # insert pilot data
                pilot = self._get_or_create(sr_tables.Pilot, pilot_code=data['pilot'].lower())
                # Insert user in role data
                cd_role = self._get_or_create(sr_tables.CDRole, role_name='Care recipient')
                user_in_role = self._get_or_create(sr_tables.UserInRole, id=int(data['user'].split(':')[-1]),
                                                   pilot_code=pilot.pilot_code,
                                                   cd_role_id=cd_role.id)
                # Insert time interval data
                if not data.get('interval_end', False) and data.get('duration', False):
                    # nominal interval
                    logging.info(inspect.stack()[0][3], ": user entered a duration")
                    time_interval = self._get_or_create(sr_tables.TimeInterval, interval_start=data['interval_start'],
                                                        typical_period=data['duration'].lower())
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
                    self._get_or_create(sr_tables.MDPilotDetectionVariable, pilot_code=data['pilot'].lower(),
                                        detection_variable_id=measure_cd_detection_variable.id,
                                        derived_detection_variable_id=measure_cd_detection_variable.derived_detection_variable_id or None)

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

    def commit_measure(self, p_user):
        """
        This method updates the Pilot column called as latest_data_submission_completed to let
        external services that the Pilot stops uploading data to the API

        :return: True if everything is OK
        """

        # update latest_data_submission_completed from Pilot table
        pilot = self.session.query(self.tables.Pilot).filter_by(pilot_code=p_user.user_in_role[0].pilot_code)[0]
        pilot.latest_data_submission_completed = arrow.utcnow()

        return self.commit()


    ###################################################################################################
    ###################################################################################################
    ######                              DATABASE GETTERS
    ###################################################################################################
    ###################################################################################################

    def get_tables(self, p_schema='city4age_sr'):
        """
        List current database tables in DATABASE active connection (Current installed system).

        :param p_schema The name of the given schema

        :return: A list containing current tables.
        """

        return super(SRPostORM, self).get_tables(p_schema)

    def get_table_instance(self, p_table_name, p_schema='city4age_sr'):
        """
        By giving a name of a table, this method returns the base instance

        :param p_table_name The name of the table
        :param p_schema The name of the given schema

        :return: A Base instance of the table to be computed
        """

        return super(SRPostORM, self).get_table_instance(p_table_name, p_schema)

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
