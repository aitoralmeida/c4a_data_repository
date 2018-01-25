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

import arrow
import logging
from src.packActivityRecognition.activity_discoverer import ActivityDiscoverer


__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2017, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"


if __name__ == '__main__':
    ar = ActivityDiscoverer()
    # Extracting the user affected by EAMs
    list_user = ar.user_in_eam_extractor()
    # Process for each user
    for user in list_user:
        logging.debug("Starting activity recognition for the user: ", user)
        # Setting some time intervals
        # TODO delete when finish
        #start_date = '2016-01-02 06:08:41.013+02'
        #end_date = '2018-05-18 06:08:41.013+02'
        end_date = arrow.utcnow()                         # current time
        start_date = end_date.shift(weeks=-1)             # duration = -1 week
        data = ar.lea_extractor(user, start_date, end_date)
        # After obtained the list of leas we are going to process it
        if len(data) > 0:
            # This user has LEA data stored in database with the given dates
            res = ar.execute_casas(data)
            if res:
                # Executing the HARSS algoritmh
                ar.execute_hars(p_user_in_role=user)
            else:
                raise Exception('The casas algorithm is failing, check the logs')
