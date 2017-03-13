# -*- coding: utf-8 -*-

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from src.packControllers import ar_post_orm, sr_post_orm
from src.packFlask.api import app as application
from src.packORM import ar_tables, sr_tables

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
    # Checking Activity Recognition tables
    ar_orm = ar_post_orm.ARPostORM()
    if len(ar_orm.get_tables()) == 0:
        # We need to create tables in database
        logging.info("Database is empty. Creating new tables in database and adding basic data")
        # Creating base tables
        ar_orm.create_tables()
        # Creating roles
        create_system_role(ar_tables, ar_orm)
        logging.info("Created system roles for Activity Recognition schema")
        # Creating administrative accounts
        create_administrative_account(ar_tables, ar_orm)
        logging.info("Created administrative accounts for Activity Recognition schema")
        # Creating Pilot information
        create_pilot(ar_tables, ar_orm)
        logging.info("Created pilots for Activity Recognition schema")
        # Commit and closing connection
        ar_orm.commit()
        ar_orm.close()

    # Checking Shared Repository tables
    sr_orm = sr_post_orm.SRPostORM()
    if len(sr_orm.get_tables()) == 0:
        # We need to create tables in database
        logging.info("Database is empty. Creating new tables in database and adding basic data")
        # Creating base tables
        sr_orm.create_tables()
        # Creating roles
        create_system_role(sr_tables, sr_orm)
        logging.info("Created system roles for Shared Repository schema")
        # Creating administrative accounts
        create_administrative_account(sr_tables, sr_orm)
        logging.info("Created administrative accounts for Shared Repository schema")
        # Creating Pilot information
        create_pilot(sr_tables, sr_orm)
        logging.info("Created pilots for Shared Repository schema")
        # Detection variables
        create_detection_variables(sr_tables, sr_orm)
        logging.info("Created detection variables for Shared Repository schema")
        # Commit and closing connection
        sr_orm.commit()
        sr_orm.close()


def create_system_role(p_tables, p_orm):
    """
    This method insert system roles in the database if they are not present

    :param p_tables: The tables instance containing available tables
    :param p_orm: The orm connection to the target schema
    :return: None
    """
    # Adding system Roles
    list_of_roles = []
    care_receiver = p_tables.CDRole(role_name='care_receiver', role_abbreviation='cr',
                                    role_description='The main user who provides data to the system. Elderly people '
                                                     'are the primary users having this role in the context of '
                                                     'City4Age.')
    care_giver = p_tables.CDRole(role_name='care_giver', role_abbreviation='cg',
                                 role_description='The care givers are the people closer to the care receivers and'
                                                  'know all the details about them. They can identify them in the '
                                                  'system, check the data inserted and annotate the results that '
                                                  'the system generates')
    geriatrician = p_tables.CDRole(role_name='geriatrician', role_abbreviation='g',
                                   role_description='Geriatricians provide medical advice for care receivers based '
                                                    'on the data they receive from care givers. They don’t need to '
                                                    'know who the care receivers are but only their profile in order '
                                                    'to suggest interventions that should be applied.')

    municipality_representative = p_tables.CDRole(role_name='municipality_representative', role_abbreviation='mr',
                                                  role_description='Representatives from each Pilot/Municipality which are '
                                                                   'responsible for the recruitment of end-users and the '
                                                                   'acquisition of data related to elementary actions will have '
                                                                   'a read-only access to all the data stored in the system. '
                                                                   'Nevertheless, this doesn’t include access to the personal '
                                                                   'identifying data of an individual.')
    researcher = p_tables.CDRole(role_name='researcher', role_abbreviation='r',
                                 role_description='Researchers will not have access to individual profiles. '
                                                  'They only need to acquire aggregated data and statistics on '
                                                  'groups of care receivers. The primary goal of a researcher is '
                                                  'to analyse the data gathered by the City4Age platform and extract '
                                                  'useful conclusions.')
    application_developer = p_tables.CDRole(role_name='application_developer', role_abbreviation='ad',
                                            role_description='Developers of the various applications of the platform '
                                                             'need to have access to data and individual profiles of '
                                                             'care receivers but without knowing the real identity '
                                                             'of them. They can only access data using the provided '
                                                             'APIs and services that City4Age will expose.')
    administrador = p_tables.CDRole(role_name='administrator', role_abbreviation='a',
                                    role_description='Administrators have direct access to the collected data stored '
                                                     'in the City4Age repositories. Nevertheless, they should not be '
                                                     'able to identify individuals by looking at the data. They are '
                                                     'in total control of any technical component of the system and '
                                                     'can adjust the access control mechanism according to the '
                                                     'project’s needs.')
    list_of_roles.extend([care_receiver, care_giver, geriatrician, municipality_representative, researcher,
                          application_developer, administrador])
    # Insert data, pending action
    p_orm.insert_all(list_of_roles)


def create_administrative_account(p_tables, p_orm):
    """
    This method creates administrative accounts in the system (This is a temporal hardcoded solution)

    :param p_tables: The tables instance containing available tables
    :param p_orm: The orm connection to the target schema
    :return: None
    """

    # with p_orm.no_autoflush:
    # Creating a simple admin user
    admin_authenticated = p_tables.UserRegistered(username='admin', password='admin')
    p_orm.insert_one(admin_authenticated)
    # Force flush to obtain the ID of the new admin user
    p_orm.flush()
    # Adding the role type of the new user
    admin_cd_role_id = p_orm.session.query(p_tables.CDRole).filter_by(role_name='administrator').first().id
    # Creating admin user_in_role in the system
    admin = p_tables.UserInRole(id='general admin of system',
                                valid_from=None, valid_to=None, user_registered_id=admin_authenticated.id,
                                cd_role_id=admin_cd_role_id)
    # Insert data, pending action
    p_orm.session.add(admin)


def create_pilot(p_tables, p_orm):
    """
    This method creates the Pilot information.

    :param p_tables: The tables instance containing available tables
    :param p_orm: The orm connection to the target schema
    :return: None
    """
    # Creating pilots names
    list_of_pilots = list()
    madrid = p_tables.Pilot(name='madrid', pilot_code='MAD', population_size=3141991)
    lecce = p_tables.Pilot(name='lecce', pilot_code='LCC', population_size=89839)
    singapore = p_tables.Pilot(name='singapore', pilot_code='SIN', population_size=5610000)
    montpellier = p_tables.Pilot(name='montpellier', pilot_code='MLP', population_size=268456)
    athens = p_tables.Pilot(name='athens', pilot_code='ATH', population_size=3090508)
    birmingham = p_tables.Pilot(name='birmingham', pilot_code='BHX', population_size=1101360)
    list_of_pilots.extend([madrid, lecce, singapore, montpellier, athens, birmingham])
    # Insert data, pending action
    p_orm.insert_all(list_of_pilots)


def create_detection_variables(p_tables, p_orm):
    """
    This method insert the detection variables description with their measures and so on.

    :param p_tables: The tables instance containing available tables
    :param p_orm: The orm connection to the target schema
    :return: None
    """
    # Adding cd detection variable types
    list_of_detection_variable_type = []
    gef = p_tables.CDDetectionVariableType(detection_variable_type='gef',
                                            detection_variable_type_description="The Geriatric Factor values "
                                                                                "contains the descriptions of primary actions. An example could be "
                                                                                "'mobility' which represent all actions related with the movement of "
                                                                                "the measured user.")
    ges = p_tables.CDDetectionVariableType(detection_variable_type='ges',
                                            detection_variable_type_description="The Geriatric Sub-Factor "
                                                                                "values contains the description of what values are performed "
                                                                                "inside a global Geriatic Factor. An example of a geriatric subfactor "
                                                                                "value inside 'mobility' geriatric factor, could be "
                                                                                "'phone_usage' or 'walking'.")
    mea = p_tables.CDDetectionVariableType(detection_variable_type='mea',
                                            detection_variable_type_description="Each factor has it own measures "
                                                                                "inside it. The measures are different in terms of values and "
                                                                                "represent the data acquisition registered to the user.")
    list_of_detection_variable_type.extend([gef, ges, mea])
    # Insert data, pending action
    p_orm.insert_all(list_of_detection_variable_type)


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
