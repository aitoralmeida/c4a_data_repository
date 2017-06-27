# -*- coding: utf-8 -*-

"""
This is the main file used by the API to extract, transform and discover new activities in the project.

The purpose of this file is to process this code periodically and discover new activities based on the CASAS
project Activity Recognition system and the Expert Activity Model developed by:

** Gorka Azkune
** Aitor Almeida


In addition, the CASAS AL system can be viewed in the following papers:

* N. Krishnan and D. Cook. Activity recognition on streaming sensor data. Pervasive and Mobile Computing, 2013.

* D. Cook, N. Krishnan, and P. Rashidi. Activity discovery and activity recognition: A new partnership. IEEE 
Transactions on Systems, Man, and Cybernetics, Part B, 2013.

* D. Cook and L. Holder. Automated activity-aware prompting for activity initiation. Gerontechnology, 11(4):1-11, 2013.

* D. Cook, A. Crandall, B. Thomas, and N. Krishnan. CASAS: A smart home in a box. IEEE Computer, 46(6):26-33, 2013.


"""


import os
import inspect
import subprocess
import arrow
import logging
import kasteren_data_transformer as kas_transformer

from packControllers import ar_post_orm
from subprocess import CalledProcessError


__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2017, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"


current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
casas_config_dir = os.path.abspath(current_dir + '../../../al/bin/al')


class ActivityDiscoverer(object):

    # Class constructor
    def __init__(self):
        # Initialing database connector
        self.database = ar_post_orm.ARPostORM()

    # Methods
    def lea_extractor(self, p_start_time, p_end_time):
        """
        Giving a time interval, this method extract all related LEAS (executed actions) from database to be 
        converted later to CASAS csv format.
        
        
        :param p_start_time: The initial time interval
        :param p_end_time The final time interval
        
        :return: A list containing all LEAS between that time intervals. 
        """
        list_leas = list()
        # Checking the given dates
        if p_end_time < p_start_time:
            # This is not possible relaunch this method using an appropriate time intervals
            logging.warn("get_action: The start date is greater than final date. Relaunch the method....")
            self.lea_extractor(p_end_time, p_start_time)
        else:
            # Format data to UTC using arrow library
            start_time = arrow.get(p_start_time)
            final_date = arrow.get(p_end_time)
            # Calling to the main method to extract leas
            list_leas = self.database.get_action(start_time, final_date)
            logging.info("get_action: Number of extracted leas is:", list_leas.count())

        return list_leas

    def execute_casas(self, p_list_leas):
        """
        By giving a set of data loaded from database, this method convert data into CSV format style to be used by the
        CASAS AL and obtain new activity tagged patterns.
        
        
        :param p_list_leas: A set of LEAS extracted from database
        :return: 
        """
        # 1º I need to know exactly the casas FORMAT Before send any


        # 2º Once data prepared use the converter, need to know the transformed.csv FILE
        # Convert data

        # TODO --> WE NEED FILES TO USE THIS CONVERTER???????
        kas_transformer.transformDataset(p_list_leas, './transformed.csv')
        # Having all needed data we can use it an transform this data into CSV







        # TODO check where is located the CONFIG_FILE to use with this AR system
        # TODO think about a sub.subprocess to catch the ouptput file



        try:

            output = subprocess.check_output(["./al/bin/al", "-r", casas_config_dir, p_list_leas])

        except CalledProcessError as e:
            e.output()




        # The output contains the LOG of the program



    def inser_data(self, p_list_activity):
        """
        Giving a list of activities, this method uses the API mechanism


        :param p_list_activity:
        :return:
        """

        # TODO insert data thought API


# TODO delete this dummy main class
if __name__ == '__main__':
    ar = ActivityDiscoverer()
    # Setting some time intervals
    start_date = '2014-05-23 06:08:41.013+02'
    end_date = '2014-05-18 06:08:41.013+02'
    data = ar.lea_extractor(start_date, end_date)
