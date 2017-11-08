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
import arrow
import logging
import csv

from collections import OrderedDict
from subprocess import PIPE, STDOUT, Popen, CalledProcessError

from pattern_model_matching import PatternModelMatching
from packControllers import ar_post_orm



#import sys
#sys.path.insert(0, '/path/to/application/app/folder')
# import file


__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2017, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"


# Global variables
DATA_FILE = 'casas.csv'
DATA_FILE_ANNOTATED = 'casas.csv.annotated'
CONFIG_FILE = 'casas.config'
LOG_FILE = 'casas_log.txt'


# Casas configuration directories
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
casas_execution_file = os.path.abspath(current_dir + '../../../al/bin/al')
casas_config_file = os.path.abspath(current_dir + '/' + CONFIG_FILE)


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
            list_leas = self.lea_extractor(p_end_time, p_start_time)
        else:
            # Format data to UTC using arrow library
            start_time = arrow.get(p_start_time)
            final_date = arrow.get(p_end_time)
            # Calling to the main method to extract leas
            list_leas = self.database.get_transformed_action(start_time, final_date)
            logging.info("get_action: Number of extracted leas is:", len(list_leas))

        return list_leas

    def execute_casas(self, p_list_leas):
        """
        By giving a set of data loaded from database, this method convert data into CSV format style to be used by the
        CASAS AL and obtain new activity tagged patterns.
        
        
        :param p_list_leas: A set of LEAS extracted from database
        :return: 
        """
        # Control check
        if len(p_list_leas) > 0:
            logging.info("execute_casas: converting the given LEAs list to CASAS format")
            # Prepare the data to be introduced in Kasteren
            list_of_sensor_actions = list()
            list_of_ordered_kasteren = list()
            for lea in p_list_leas:
                local_time = lea['execution_datetime'].to('Europe/Madrid')
                time = local_time.format('YYYY-MM-DD')
                hour = local_time.format('HH:mm:ss')
                kasteren_lea = OrderedDict([
                    ('lea_time', time),
                    ('lea_hour', hour),
                    ('action1', lea['action_name'].upper()),
                    ('action2', lea['action_name'].upper()),
                    ('mode', 'ON'),
                    ('tag', 'OTHER_ACTIVITY')])
                list_of_ordered_kasteren.append(kasteren_lea)
                # Adding the sensor elements to the list to be used in the config file
                if lea['action_name'] not in list_of_sensor_actions:
                    list_of_sensor_actions.append(lea['action_name'])
            # Convert to csv
            keys = list_of_ordered_kasteren[0].keys()
            with open(DATA_FILE, 'wb', 0) as output_file:
                dict_writer = csv.DictWriter(output_file, keys, delimiter=' ')
                # dict_writer.writeheader()
                dict_writer.writerows(list_of_ordered_kasteren)
                output_file.flush()
                os.fsync(output_file.fileno())
            # Saving the config file
            with open(CONFIG_FILE, 'wb', 0) as output_config_file:
                # Writing the structure in the file
                output_config_file.write('sensor ' + " ".join(str(i) for i in list_of_sensor_actions))
                output_config_file.write('\nweight 1')
                output_config_file.write('\ndata ' + DATA_FILE)
                output_config_file.write('\nmodel model')
                output_config_file.write('\npredictactivity Sleep')
                output_config_file.flush()
                os.fsync(output_config_file.fileno())
            # We save the needed file into disk, now we are going to use casas algorithm
            try:
                output = Popen([casas_execution_file, '-d', casas_config_file], shell=False,
                               stdout=PIPE, stderr=STDOUT)
                out, err = output.communicate()
                errcode = output.returncode
                # Creating the needed output file
                with open(LOG_FILE, 'wb', 0) as output_log_file:
                    # Writing the log file of the algorithm
                    output_log_file.write(out)
                    output_log_file.flush()
                    os.fsync(output_log_file.fileno())
                ########
            except CalledProcessError as e:
                e.output()

            # The output contains the LOG of the program
        else:
            # The given list doesn't have leas, nothing to do
            logging.warning("execute_casas: the given list of extracted LEAs is empty")

    def execute_hars(self, p_list_leas):
        """
        This method executes the HARS algorithm to discover new activities.

        :param p_list_leas: The extracted list of leas from DB
        :type p_list_leas: list

        :return: None
        """

        # Loading saved files from disk
        eams_file = open(DATA_FILE, 'r')
        annotated_file = open(DATA_FILE_ANNOTATED, 'r')
        log_file = open(LOG_FILE, 'r')
        # Instantiation of PatternModelMatching
        PatternModelMatching(eams_file, annotated_file, log_file, None)
        # TODO continue here


        pass


    def inser_data(self, p_list_discovered_activities, p_list_leas):
        """
        Given the final results from HARS, insert needed data into database


        :p_p_list_discovered_activities: The discovered activities from HARS
        :param p_list_activity: The extracted list of LEAS
        :return:
        """

        # TODO insert data thought API into database
        pass


# TODO delete this dummy main class
if __name__ == '__main__':
    ar = ActivityDiscoverer()
    # Setting some time intervals
    start_date = '2014-05-23 06:08:41.013+02'
    end_date = '2014-05-18 06:08:41.013+02'
    data = ar.lea_extractor(start_date, end_date)
    # After obtained the list of leas we are going to process it
    res = ar.execute_casas(data)
    # TU HARS
    # BD
