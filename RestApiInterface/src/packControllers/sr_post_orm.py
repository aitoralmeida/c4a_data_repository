# -*- coding: utf-8 -*-

from packORM import sr_tables
from post_orm import PostORM
from sqlalchemy import MetaData
import datetime


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

        # TODO sample code here to modify

        for data in p_data:
            insert_data_list = []


            # Need to define the tables that needs this method in shared repo database
            """
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



            # Append data to the list and insert it.
            insert_data_list.append(executed_action)
            self.insert_all(insert_data_list)
            """
        # Whe prepared all data, now we are going to commit it into DB.
        return self.commit()
