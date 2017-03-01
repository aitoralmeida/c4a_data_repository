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
    def __init__(self):
        PostORM.__init__(self)

    def create_tables(self):
        """
        Create database tables
        :return:
        """
        return sr_tables.create_tables(self.engine)

    def get_tables(self):
        """
        List current database tables in DATABASE active connection (Current installed system).

        :return: A list containing current tables.
        """
        m = MetaData()
        m.reflect(self.engine, schema='city4age_sr')
        return m.tables.keys()

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
