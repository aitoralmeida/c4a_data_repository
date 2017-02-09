# -*- coding: utf-8 -*-

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from packControllers import ar_post_orm, sr_post_orm
from src.packFlask.api import app as application
from src.packORM import ar_tables

__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2016, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"

# Prepare base dir working directory
basedir = os.path.dirname(os.path.realpath(__file__))
if not os.path.exists(os.path.join(basedir, "main.py")):
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, "main.py")):
        basedir = cwd
sys.path.insert(0, basedir)


def generate_database():
    """
    Checks if there is a database created and inserts the base data.

    :return:
    """
    # TODO create here two databas schemas
    orm = ar_post_orm.ARPostORM()
    if len(orm.get_tables()) == 0:
        # We need to create tables in database
        logging.info("Database is empty. Creating new tables in database and adding basic data")
        # Creating base tables
        orm.create_tables()
        # Adding system Roles
        list_of_roles = []
        care_receiver = ar_tables.CDRole(role_name='care_receiver', role_abbreviation='cr',
                                         role_description='The main user who provides data to the system. Elderly people '
                                                       'are the primary users having this role in the context of '
                                                       'City4Age.')
        care_giver = ar_tables.CDRole(role_name='care_giver', role_abbreviation='cg',
                                      role_description='The care givers are the people closer to the care receivers and'
                                                    'know all the details about them. They can identify them in the '
                                                    'system, check the data inserted and annotate the results that '
                                                    'the system generates')
        geriatrician = ar_tables.CDRole(role_name='geriatrician', role_abbreviation='g',
                                        role_description='Geriatricians provide medical advice for care receivers based '
                                                      'on the data they receive from care givers. They don’t need to '
                                                      'know who the care receivers are but only their profile in order '
                                                      'to suggest interventions that should be applied.')

        municipality_representative = ar_tables.CDRole(role_name='municipality_representative', role_abbreviation='mr',
                                                       role_description='Representatives from each Pilot/Municipality which are '
                                                                     'responsible for the recruitment of end-users and the '
                                                                     'acquisition of data related to elementary actions will have '
                                                                     'a read-only access to all the data stored in the system. '
                                                                     'Nevertheless, this doesn’t include access to the personal '
                                                                     'identifying data of an individual.')
        researcher = ar_tables.CDRole(role_name='researcher', role_abbreviation='r',
                                      role_description='Researchers will not have access to individual profiles. '
                                                    'They only need to acquire aggregated data and statistics on '
                                                    'groups of care receivers. The primary goal of a researcher is '
                                                    'to analyse the data gathered by the City4Age platform and extract '
                                                    'useful conclusions.')
        application_developer = ar_tables.CDRole(role_name='application_developer', role_abbreviation='ad',
                                                 role_description='Developers of the various applications of the platform '
                                                               'need to have access to data and individual profiles of '
                                                               'care receivers but without knowing the real identity '
                                                               'of them. They can only access data using the provided '
                                                               'APIs and services that City4Age will expose.')
        administrador = ar_tables.CDRole(role_name='administrator', role_abbreviation='a',
                                         role_description='Administrators have direct access to the collected data stored '
                                                       'in the City4Age repositories. Nevertheless, they should not be '
                                                       'able to identify individuals by looking at the data. They are '
                                                       'in total control of any technical component of the system and '
                                                       'can adjust the access control mechanism according to the '
                                                       'project’s needs.')
        list_of_roles.extend([care_receiver, care_giver, geriatrician, municipality_representative, researcher,
                              application_developer, administrador])
        orm.insert_all(list_of_roles)
        # Creating a simple admin user
        admin_authenticated = ar_tables.UserRegistered(username='admin', password='admin')
        orm.insert_one(admin_authenticated)
        # Committing changes
        orm.commit()
        # Getting new admin ID
        admin_authenticated_id = orm.session.query(ar_tables.UserRegistered).filter_by(username='admin').first().id
        admin_cd_role_id = orm.session.query(ar_tables.CDRole).filter_by(role_name='administrator').first().id
        # Creating admin user_in_role in the system
        admin = ar_tables.UserInRole(id='general admin of system',
                                     valid_from=None, valid_to=None, user_registered_id=admin_authenticated_id,
                                     cd_role_id=admin_cd_role_id)
        orm.session.add(admin)
        # Creating pilots names
        list_of_pilots = list()
        madrid = ar_tables.Pilot(name='madrid', pilot_code='MAD', population_size=3141991)
        lecce = ar_tables.Pilot(name='lecce', pilot_code='LCC', population_size=89839)
        singapore = ar_tables.Pilot(name='singapore', pilot_code='SIN', population_size=5610000)
        montpellier = ar_tables.Pilot(name='montpellier', pilot_code='MLP', population_size=268456)
        athens = ar_tables.Pilot(name='athens', pilot_code='ATH', population_size=3090508)
        birmingham = ar_tables.Pilot(name='birmingham', pilot_code='BHX', population_size=1101360)
        list_of_pilots.extend([madrid, lecce, singapore, montpellier, athens, birmingham])
        orm.session.add_all(list_of_pilots)
        orm.commit()
        orm.close()

    sr_orm = sr_post_orm.SRPostORM()
    if len(sr_orm.get_tables()) == 0:
        # We need to create tables in database
        logging.info("Database is empty. Creating new tables in database and adding basic data")
        # Creating base tables
        sr_orm.create_tables()

        # Add basic data to SR schema


# main execution
if __name__ == '__main__':
    # Create the log folder if not exists
    if not os.path.exists('./log'):
        os.makedirs('./log')
    # Check if database is created and inserts data if it is necessary
    generate_database()
    # Setting logging handlers
    logHandler = RotatingFileHandler('./log/info.log', maxBytes=1024 * 1024 * 100, backupCount=20)
    # set the log handler level
    logHandler.setLevel(logging.INFO)
    # set the formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logHandler.setFormatter(formatter)
    # set the app logger level
    application.logger.setLevel(logging.INFO)
    application.logger.addHandler(logHandler)
    # Run the application
    application.run(debug=True, host='0.0.0.0')
