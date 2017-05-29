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

import subprocess

import KasterenDataTransformer as kas_transformer


__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2017, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"


class ActivityDiscoverer(object):

    # Class constructor
    def __init__(self):
        # Here we can initialize some values, like database?
        pass

    # Methods
    def lea_extractor(self, p_start_time, p_end_time):
        """
        Giving a time interval, this method extract all related LEAS (executed actions) from database to be 
        converted later to CASAS csv format.
        
        
        :param p_start_time: The initial time interval
        :param p_end_time The final time interval
        
        :return: A list containing all LEAS between that time intervals. 
        """

        # Call to database to obtain the needed leas:

        # CALL to database

        # return leas

        pass

    def execute_casas(self, p_data):
        """
        By giving a set of data loaded from database, this method convers data into CSV format style to be used by the 
        CASAS AL and obtain new activity tagged patterns.
        
        
        :param p_data: A set of LEAS extracted from database
        :return: 
        """
        # Convert data
        kas_transformer.transformDataset(p_data, './transformed.csv')
        # Having all needed data we can use it an transform this data into CSV


        # TODO check where is located the CONFIG_FILE to use with this AR system
        # TODO think about a sub.subprocess to catch the ouptput file
        # Usage
        # for AR:    . / al - r < config_file > [ < data_file >]

        # Usage
        # for AP:    . / al - p < config_file > [ < data_file >]


        # TODO use WAIT retval = p.wait()

        output = subprocess.check_output(["al", "-p", "config", p_data])

        # The output contains the LOG of the program

        