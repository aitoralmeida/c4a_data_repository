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
import io
import inspect
import arrow
import logging
import csv
import pandas as pd

from collections import OrderedDict
from subprocess import PIPE, STDOUT, Popen, CalledProcessError

from pattern_model_matching import PatternModelMatching
from expert_activity_model import ExpertActivityModel


from src.packControllers import ar_post_orm


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


class ActivityDiscoverer(object):

    # Class constructor
    def __init__(self):
        # Initialing database connector
        self.database = ar_post_orm.ARPostORM()

    # Methods

    def user_in_eam_extractor(self):
        """
        This method extracts the saved users with EAMs from the DATABASE.


        :return: A list containing the unique users with EAMS
        :rtype list
        """
        list_user = self.database.get_user_in_eam()
        logging.info("get_action: Number of extracted leas is:", len(list_user))
        return list_user

    def lea_extractor(self, p_user_in_role, p_start_time, p_end_time):
        """
        Giving a time interval, this method extract all related LEAS (executed actions) from database to be 
        converted later to CASAS csv format.
        

        :param p_user_in_role The user id in the system
        :param p_start_time: The initial time interval
        :param p_end_time The final time interval
        
        :return: A list containing all LEAS between that time intervals. 
        """
        list_lea = []
        # Checking the given dates
        if p_end_time < p_start_time:
            # This is not possible relaunch this method using an appropriate time intervals
            logging.warn("get_action: The start date is greater than final date. Relaunch the method....")
            list_lea = self.lea_extractor(p_user_in_role, p_end_time, p_start_time)
        else:
            # Format data to UTC using arrow library
            start_time = arrow.get(p_start_time)
            final_date = arrow.get(p_end_time)
            # Calling to the main method to extract leas
            list_lea = self.database.get_transformed_action(p_user_in_role, start_time, final_date)
            logging.info("get_action: Number of extracted leas is:", len(list_lea))

        return list_lea

    def execute_casas(self, p_list_leas):
        """
        By giving a set of data loaded from database, this method convert data into CSV format style to be used by the
        CASAS AL and obtain new activity tagged patterns.
        
        
        :param p_list_leas: A set of LEAS extracted from database
        :return: True if casas y executed correct
                False otherwise
        """

        res = False
        list_of_executed_actions = []
        list_of_locations = []

        # Control check
        if len(p_list_leas) > 0:
            logging.info("execute_casas: converting the given LEAs list to CASAS format")
            # Prepare the data to be introduced in Kasteren
            list_of_sensor_actions = list()
            list_of_ordered_kasteren = list()
            for lea in p_list_leas:
                local_time = lea['execution_datetime'].to('Europe/London')          # GMT+0
                time = local_time.format('YYYY-MM-DD')
                hour = local_time.format('HH:mm:ss')
                kasteren_lea = OrderedDict([
                    ('lea_time', time),
                    ('lea_hour', hour),
                    ('action1', lea['action_name'].lower()),
                    ('action2', lea['action_name'].lower()),
                    ('mode', 'ON'),
                    ('tag', 'Other_Activity')])
                list_of_ordered_kasteren.append(kasteren_lea)
                # Adding the sensor elements to the list to be used in the config file
                if lea['action_name'] not in list_of_sensor_actions:
                    list_of_sensor_actions.append(lea['action_name'])
                # Adding the location
                list_of_locations.append(lea['location_name'])
                # Adding the executed_action into the list of locations
                list_of_executed_actions.append(lea['executed_action_id'])
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
                output_config_file.write('sensor ' + " ".join(str(i).lower() for i in list_of_sensor_actions))
                output_config_file.write('\nweight 1')
                output_config_file.write('\ndata ' + DATA_FILE)
                output_config_file.write('\nmode 0')
                output_config_file.write('\nmodel model')
                output_config_file.write('\npredictactivity Sleep')
                output_config_file.flush()
                os.fsync(output_config_file.fileno())
            # We save the needed file into disk, now we are going to use casas algorithm
            try:
                output = Popen([casas_execution_file, '-d', CONFIG_FILE], shell=False,
                               stdout=PIPE, stderr=STDOUT)
                out, err = output.communicate()
                errcode = output.returncode
                # Creating the needed output file
                with open(LOG_FILE, 'wb', 0) as output_log_file:
                    # Writing the log file of the algorithm
                    output_log_file.write(out)
                    output_log_file.flush()
                    os.fsync(output_log_file.fileno())

                # After sync and store the file, we are going to change the third column with the locations
                logging.info("giving the locations in the third column")
                # Opening the dataframe annontated file
                # df = pd.read_csv(DATA_FILE_ANNOTATED, parse_dates=[[0, 1]], header=None, index_col=0, sep='\t')
                df = pd.read_csv(DATA_FILE_ANNOTATED, header=None, index_col=0, sep='\t')
                # Change third column
                df[2] = list_of_locations
                # Changes the third column with the given locations
                df['executed_action'] = list_of_executed_actions
                # Store the annotated data with its locations
                df.to_csv(DATA_FILE_ANNOTATED, sep='\t', header=False, encoding='utf-8')
                res = True

            except CalledProcessError as e:
                e.output()
                logging.error("The casas execuion gives the following error: " + errcode)
        else:
            # The given list doesn't have leas, nothing to do
            logging.warning("execute_casas: the given list of extracted LEAs is empty")

        return res

    def execute_hars(self, p_user_in_role):
        """
        This method executes the HARS algorithm to discover new activities.


        :param p_user_in_role The user in role id of affected user
        :type int

        :return: None
        """
        # Retrieving the stored EAMs of the current user from database
        eamlist = self._eam_extractor(p_user_in_role)
        # Create a PatternModelMatching instance
        pmd = PatternModelMatching(eamlist, DATA_FILE_ANNOTATED, LOG_FILE)
        # 1º pmd.load_annotated_data <-- THIS WILL BE DELETED, USING IT WHEN YOU LOAD YOUR CSV FILE
        # 2º pmd.process_patterns
        # 3º pmd.store_result <-- to database

        # 1º Load the annotated data into a pandas object
        pmd.load_annotated_data()
        # 2º Process each pattern as needed
        pmd.process_patterns()
        # 3º Store the result in database
        pmd.store_result_database(self.database, p_user_in_role)
        pmd.store_result('casas_final_%s.csv' % p_user_in_role)
        logging.info("execute_hars: The execution of HARS has finished successfully for the user: ", p_user_in_role)

    def _eam_extractor(self, p_user_in_role_id):
        """
        Get stored EAMS in database and convert it to JSON format based on:

         "UseToilet": {
             "locations": ["Bathroom"],
             "actions": ["ToiletDoor", "ToiletFlush"],
             "duration": 60,
             "start": [["00:00", "23:59"]]
         },
         @@@@@

        :return: A list containing instances of ExpectActivityModel
        :rtype: list
        """

        eamlist = []
        # Obtaining the stored EAMs JSON dict
        eamsdict = self.database.get_eam(p_user_in_role_id)
        for element in eamsdict:
            # Instantiation of ExppertActivityModel for each element
            eam = ExpertActivityModel(element, eamsdict[element])
            eamlist.append(eam)

        return eamlist
