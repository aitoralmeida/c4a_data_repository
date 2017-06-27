# -*- coding: utf-8 -*-

"""

This file contains the basic data structure to initialize the REST API interface.

"""

import logging
import ar_tables
import sr_tables

__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2017, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"


def generate_database(p_ar_post_orm, p_sr_post_orm):
    """
    Checks if there is a database created and inserts the base data.
    
    :param p_ar_post_orm: An instantiation of the Activity Recognition database
    :param p_sr_post_orm: An instantiation of the Shared Recognition database

    :return:
    """
    # Checking Activity Recognition tables
    ar_orm = p_ar_post_orm
    if len(ar_orm.get_tables()) == 0:
        print("Creating Activity Recognition database schema........")
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
        # Creating Pilots accounts
        create_pilots_accounts(ar_tables, ar_orm)
        logging.info("Created pilot accounts for Activity Recognition schema")
        # Creating CDActivity information:
        create_actions(ar_tables, ar_orm)
        logging.info("Created Actions for Activity Recognition schema")
        # Commit and closing connection
        ar_orm.commit()
        ar_orm.close()
        print ("Done")

    # Checking Shared Repository tables
    sr_orm = p_sr_post_orm
    if len(sr_orm.get_tables()) == 0:
        print ("Creating Shared Repository database schema........")
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
        # Creating Pilots accounts
        create_pilots_accounts(sr_tables, ar_orm)
        logging.info("Created pilot accounts for Shared Repository schema")
        # Detection variables
        create_detection_variables(sr_tables, sr_orm)
        logging.info("Created detection variables for Shared Repository schema")
        # TODO we need to be sure if this schema needs this datatype
        # Creating CDActivity information:
        create_actions(sr_tables, sr_orm)
        logging.info("Created Actions for Shared Repository schema")
        # Creating CDDetectionVariable Table
        create_measure(sr_tables, sr_orm)
        logging.info("Created CDDetectionVariable for Shared Repository schema")
        # Commit and closing connection
        sr_orm.commit()
        sr_orm.close()
        print("Done")


def create_system_role(p_tables, p_orm):
    """
    This method insert system roles in the database if they are not present

    :param p_tables: The tables instance containing available tables
    :param p_orm: The orm connection to the target schema
    :return: None
    """
    # Adding system Roles
    list_of_roles = []

    # End-user roles

    care_recipient = p_tables.CDRole(role_name='Care recipient', role_abbreviation='cr',
                                     role_description='Care recipient, senior citizen observed')

    informal_caregiver = p_tables.CDRole(role_name='Informal caregiver', role_abbreviation='ifc',
                                         role_description='Informal caregiver, family member, friend, volunteer')

    formal_caregiver = p_tables.CDRole(role_name='Formal caregiver', role_abbreviation='cg',
                                       role_description='Health or social care provider staff')

    elderly_centre_executive = p_tables.CDRole(role_name='Elderly/community centre executive', role_abbreviation='ece',
                                               role_description='Operator/manager of elderly/community centre')

    sheltered_accomodation_manager = p_tables.CDRole(role_name='Sheltered accommodation manager',
                                                     role_abbreviation='sam',
                                                     role_description='Operator/manager of nursery home, AAL housing, '
                                                                      'social housing, etc.')

    general_practicioner = p_tables.CDRole(role_name='General practioner', role_abbreviation='gp',
                                           role_description='Chosen general practice doctor treating the CR')

    local_geriatrician = p_tables.CDRole(role_name='Local/pilot geriatrician', role_abbreviation='lge',
                                         role_description='Local or pilot location geriatrician treating the CR')

    project_geriatrician = p_tables.CDRole(role_name='Project geriatrician', role_abbreviation='pge',
                                           role_description='City4Age project expert geriatrician')

    behavioural_scientist = p_tables.CDRole(role_name='Behavioural scientist', role_abbreviation='bhs',
                                            role_description='Behavioural scientist expert/researcher')

    medical_researcher = p_tables.CDRole(role_name='Medical researcher', role_abbreviation='mdr',
                                         role_description='Medical researcher')

    epidemiologist = p_tables.CDRole(role_name='Epidemiologist', role_abbreviation='epi',
                                     role_description='Epidemiologist')

    city_policy_planner = p_tables.CDRole(role_name='City policy planner', role_abbreviation='cpp',
                                          role_description='Planner/executive of city policy towards the elderly')

    social_service_representative = p_tables.CDRole(role_name='Social service representative', role_abbreviation='ssr',
                                                    role_description='Social services representative')

    municipality_representative = p_tables.CDRole(role_name='Municipality representative', role_abbreviation='mpr',
                                                  role_description='Planner/executive of municipality '
                                                                   'policy towards the elderly')

    pilot_source_system = p_tables.CDRole(role_name='Pilot source system', role_abbreviation='pss',
                                          role_description='Data source system submitting pilot (city) '
                                                           'data to the unified data store ')

    # Administrative roles
    administrador = p_tables.CDRole(role_name='administrator', role_abbreviation='a',
                                    role_description='The primary super-user in the system who has all the access to '
                                                     'manage the system')

    system = p_tables.CDRole(role_name='system', role_abbreviation='s',
                             role_description='A role used for Pilots tech leads to configure the api endpoints')

    list_of_roles.extend([care_recipient, informal_caregiver, formal_caregiver, elderly_centre_executive,
                          sheltered_accomodation_manager, general_practicioner, local_geriatrician,
                          project_geriatrician, behavioural_scientist, medical_researcher, epidemiologist,
                          city_policy_planner, social_service_representative, municipality_representative,
                          pilot_source_system, administrador, system])

    # Insert data, pending action
    p_orm.insert_all(list_of_roles)
    # Commit changes
    p_orm.commit()


def create_administrative_account(p_tables, p_orm):
    """
    This method creates administrative accounts in the system.

    :param p_tables: The tables instance containing available tables
    :param p_orm: The orm connection to the target schema
    :return: None
    """

    # with p_orm.no_autoflush:
    # Creating administrative accounts
    admin_authenticated = p_tables.UserInSystem(username='admin', password='admin')
    system_authenticated = p_tables.UserInSystem(username='system', password='system')
    # Pending insert into database
    p_orm.insert_all([admin_authenticated, system_authenticated])
    # Force flush to obtain the ID of the new accounts
    p_orm.flush()
    # Adding the role type of the new user
    admin_cd_role_id = p_orm.session.query(p_tables.CDRole).filter_by(role_name='administrator').first().id
    system_cd_role_id = p_orm.session.query(p_tables.CDRole).filter_by(role_name='system').first().id
    # Creating admin user_in_role in the system
    admin = p_tables.UserInRole(valid_from=None, valid_to=None, user_in_system_id=admin_authenticated.id,
                                cd_role_id=admin_cd_role_id)
    system = p_tables.UserInRole(valid_from=None, valid_to=None, user_in_system_id=system_authenticated.id,
                                 cd_role_id=system_cd_role_id)
    # Insert data, pending action
    p_orm.insert_all([admin, system])
    # Commit changes
    p_orm.commit()


def create_pilots_accounts(p_tables, p_orm):
    """
    This method creates the requires accounts to the Pilots in the system

    Usernames to enter in the API
    -------------------------------

    “ATH_PSS" for Athens
    “BHX_PSS” for Birmingham
    “LCC_PSS” for Lecce
    “MAD_PSS” for Madrid
    “MPL_PSS” for Montpellier
    “SIN_PSS” for Singapore
    
    
    Passwords are created manually.

    """
    # Creating Pilot accounts
    athens = p_tables.UserInSystem(username='ATH_PSS', password='VsDaxmeM')
    birmingham = p_tables.UserInSystem(username='BHX_PSS', password='n56w6qbw')
    lecce = p_tables.UserInSystem(username='LCC_PSS', password='TTjWhjYZ')
    madrid = p_tables.UserInSystem(username='MAD_PSS', password='SUJ99dBa')
    montpellier = p_tables.UserInSystem(username='MPL_PSS', password='Yxr9Ajpw')
    singapore = p_tables.UserInSystem(username='SIN_PSS', password='GzpNAmUz')
    # Pending insert into database
    p_orm.insert_all([athens, birmingham, lecce, madrid, montpellier, singapore])
    # Force flush to obtain the ID of the new accounts
    p_orm.flush()
    # Adding the role type.
    pilot_source_system_id = p_orm.session.query(p_tables.CDRole).filter_by(role_name='Pilot source system').first().id
    # Creating pilot user_in_role in the system
    athens_uir = p_tables.UserInRole(valid_from=None, valid_to=None, user_in_system_id=athens.id,
                                     cd_role_id=pilot_source_system_id, pilot_code='ath')
    birmingham_uir = p_tables.UserInRole(valid_from=None, valid_to=None, user_in_system_id=birmingham.id,
                                         cd_role_id=pilot_source_system_id, pilot_code='bhx')
    lecce_uir = p_tables.UserInRole(valid_from=None, valid_to=None, user_in_system_id=lecce.id,
                                    cd_role_id=pilot_source_system_id, pilot_code='lcc')

    madrid_uir = p_tables.UserInRole(valid_from=None, valid_to=None, user_in_system_id=madrid.id,
                                     cd_role_id=pilot_source_system_id, pilot_code='mad')

    montpellier_uir = p_tables.UserInRole(valid_from=None, valid_to=None, user_in_system_id=montpellier.id,
                                          cd_role_id=pilot_source_system_id, pilot_code='mpl')

    singapore_uir = p_tables.UserInRole(valid_from=None, valid_to=None, user_in_system_id=singapore.id,
                                        cd_role_id=pilot_source_system_id, pilot_code='sin')

    # Insert data, pending action
    p_orm.insert_all([athens_uir, birmingham_uir, lecce_uir, madrid_uir, montpellier_uir, singapore_uir])
    # Commit changes
    p_orm.commit()


def create_pilot(p_tables, p_orm):
    """
    This method creates the Pilot information.

    :param p_tables: The tables instance containing available tables
    :param p_orm: The orm connection to the target schema
    :return: None
    """
    # Creating pilots names
    list_of_pilots = list()
    madrid = p_tables.Pilot(pilot_name='madrid', code='mad', population_size=3141991)
    lecce = p_tables.Pilot(pilot_name='lecce', code='lcc', population_size=89839)
    singapore = p_tables.Pilot(pilot_name='singapore', code='sin', population_size=5610000)
    montpellier = p_tables.Pilot(pilot_name='montpellier', code='mpl', population_size=268456)
    athens = p_tables.Pilot(pilot_name='athens', code='ath', population_size=3090508)
    birmingham = p_tables.Pilot(pilot_name='birmingham', code='bhx', population_size=1101360)
    list_of_pilots.extend([madrid, lecce, singapore, montpellier, athens, birmingham])
    # Insert data, pending action
    p_orm.insert_all(list_of_pilots)
    # Commint changes
    p_orm.commit()


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
    gfg = p_tables.CDDetectionVariableType(detection_variable_type='gfg',
                                           detection_variable_type_description='Geriatric factor group')

    nui = p_tables.CDDetectionVariableType(detection_variable_type='nui',
                                           detection_variable_type_description='Numeric indicator')

    ovl = p_tables.CDDetectionVariableType(detection_variable_type='ovl',
                                           detection_variable_type_description='Overall frailty score')

    # Adding data in the list
    list_of_detection_variable_type.extend([gef, ges, mea, gfg, nui, ovl])
    # Insert data, pending action
    p_orm.insert_all(list_of_detection_variable_type)
    # Commit changes
    p_orm.commit()


def create_measure(p_tables, p_orm):
    """
    This method inserts the measure dictionary with its different values and meanings

    :param p_tables: The tables instance containing available tables
    :param p_orm: The orm connection to the target schema
    :return: 
    """

    list_of_measures = []

    appetite = p_tables.CDDetectionVariable(detection_variable_name='appetite', base_unit='integer',
                                            detection_variable_type='mea')
    bathroom_time = p_tables.CDDetectionVariable(detection_variable_name='bathroom_time', base_unit='integer',
                                                 detection_variable_type='mea')
    bathroom_visits = p_tables.CDDetectionVariable(detection_variable_name='bathroom_visits', base_unit='integer',
                                                   detection_variable_type='mea')
    bedroom_time = p_tables.CDDetectionVariable(detection_variable_name='bedroom_time', base_unit='integer',
                                                detection_variable_type='mea')
    bedroom_visits = p_tables.CDDetectionVariable(detection_variable_name='bedroom_visits', base_unit='integer',
                                                  detection_variable_type='mea')
    cinema_time = p_tables.CDDetectionVariable(detection_variable_name='cinema_time', base_unit='integer',
                                               detection_variable_type='mea')
    cinema_visits = p_tables.CDDetectionVariable(detection_variable_name='cinema_visits', base_unit='integer',
                                                 detection_variable_type='mea')
    cinema_visits_month = p_tables.CDDetectionVariable(detection_variable_name='cinema_visits_month',
                                                       base_unit='integer', detection_variable_type='mea')
    culturepoi_visits_month = p_tables.CDDetectionVariable(detection_variable_name='culturepoi_visits_month',
                                                           base_unit='integer', detection_variable_type='mea')
    culturepoi_visits_time_perc_month = p_tables.CDDetectionVariable(
        detection_variable_name='culturepoi_visits_time_perc_month', base_unit='float', detection_variable_type='mea')

    exhaustion = p_tables.CDDetectionVariable(detection_variable_name='exhaustion', base_unit='float',
                                              detection_variable_type='mea')
    falls_month = p_tables.CDDetectionVariable(detection_variable_name='falls_month', base_unit='integer',
                                               detection_variable_type='mea')
    foodcourt_time = p_tables.CDDetectionVariable(detection_variable_name='foodcourt_time', base_unit='integer',
                                                  detection_variable_type='mea')
    foodcourt_visits_month = p_tables.CDDetectionVariable(detection_variable_name='foodcourt_visits_month',
                                                          base_unit='integer', detection_variable_type='mea')
    foodcourt_visits_week = p_tables.CDDetectionVariable(detection_variable_name='foodcourt_visits_week',
                                                         base_unit='integer', detection_variable_type='mea')
    gp_time_month = p_tables.CDDetectionVariable(detection_variable_name='gp_time_month',
                                                 base_unit='integer', detection_variable_type='mea')
    gp_visits_month = p_tables.CDDetectionVariable(detection_variable_name='gp_visits_month',
                                                   base_unit='integer', detection_variable_type='mea')
    heart_rate = p_tables.CDDetectionVariable(detection_variable_name='heart_rate', base_unit='float',
                                              detection_variable_type='mea')
    home_time = p_tables.CDDetectionVariable(detection_variable_name='home_time', base_unit='integer',
                                             detection_variable_type='mea')
    kitchen_time = p_tables.CDDetectionVariable(detection_variable_name='kitchen_time', base_unit='integer',
                                                detection_variable_type='mea')
    kitchen_visits = p_tables.CDDetectionVariable(detection_variable_name='kitchen_visits', base_unit='integer',
                                                  detection_variable_type='mea')
    livingroom_time = p_tables.CDDetectionVariable(detection_variable_name='livingroom_time', base_unit='integer',
                                                   detection_variable_type='mea')
    livingroom_visits = p_tables.CDDetectionVariable(detection_variable_name='livingroom_visits', base_unit='integer',
                                                     detection_variable_type='mea')
    meals_num = p_tables.CDDetectionVariable(detection_variable_name='meals_num', base_unit='integer',
                                             detection_variable_type='mea')
    memory = p_tables.CDDetectionVariable(detection_variable_name='memory', base_unit='object',
                                          detection_variable_type='mea')
    othersocial_long_visits = p_tables.CDDetectionVariable(detection_variable_name='othersocial_long_visits',
                                                           base_unit='integer', detection_variable_type='mea')
    othersocial_time = p_tables.CDDetectionVariable(detection_variable_name='othersocial_time', base_unit='integer',
                                                    detection_variable_type='mea')
    othersocial_time_out_perc = p_tables.CDDetectionVariable(detection_variable_name='othersocial_time_out_perc',
                                                             base_unit='float', detection_variable_type='mea')
    othersocial_visits = p_tables.CDDetectionVariable(detection_variable_name='othersocial_visits',
                                                      base_unit='integer', detection_variable_type='mea')
    outdoor_num = p_tables.CDDetectionVariable(detection_variable_name='outdoor_num', base_unit='integer',
                                               detection_variable_type='mea')
    outdoor_time = p_tables.CDDetectionVariable(detection_variable_name='outdoor_time', base_unit='integer',
                                                detection_variable_type='mea')
    pain = p_tables.CDDetectionVariable(detection_variable_name='pain', base_unit='integer',
                                        detection_variable_type='mea')
    perceived_temperature = p_tables.CDDetectionVariable(detection_variable_name='perceived_temperature',
                                                         base_unit='float', detection_variable_type='mea')
    pharmacy_time = p_tables.CDDetectionVariable(detection_variable_name='pharmacy_time', base_unit='integer',
                                                 detection_variable_type='mea')
    pharmacy_visits_month = p_tables.CDDetectionVariable(detection_variable_name='pharmacy_visits_month',
                                                         base_unit='integer', detection_variable_type='mea')
    pharmacy_visits_week = p_tables.CDDetectionVariable(detection_variable_name='pharmacy_visits_week',
                                                        base_unit='integer', detection_variable_type='mea')
    pharmacy_visits = p_tables.CDDetectionVariable(detection_variable_name='pharmacy_visits', base_unit='integer',
                                                   detection_variable_type='mea')
    phonecalls_long_placed_perc = p_tables.CDDetectionVariable(detection_variable_name='phonecalls_long_placed_perc',
                                                               base_unit='float', detection_variable_type='mea')
    phonecalls_long_received_perc = p_tables.CDDetectionVariable(
        detection_variable_name='phonecalls_long_received_perc',
        base_unit='float', detection_variable_type='mea')
    phonecalls_missed = p_tables.CDDetectionVariable(detection_variable_name='phonecalls_missed', base_unit='integer',
                                                     detection_variable_type='mea')
    phonecalls_placed = p_tables.CDDetectionVariable(detection_variable_name='phonecalls_placed', base_unit='integer',
                                                     detection_variable_type='mea')
    phonecalls_placed_perc = p_tables.CDDetectionVariable(detection_variable_name='phonecalls_placed_perc',
                                                          base_unit='float', detection_variable_type='mea')
    phonecalls_received = p_tables.CDDetectionVariable(detection_variable_name='phonecalls_received',
                                                       base_unit='integer'
                                                       , detection_variable_type='mea')
    phonecalls_received_perc = p_tables.CDDetectionVariable(detection_variable_name='phonecalls_received_perc',
                                                            base_unit='float', detection_variable_type='mea')
    phonecalls_short_placed_perc = p_tables.CDDetectionVariable(detection_variable_name='phonecalls_short_placed_perc',
                                                                base_unit='float', detection_variable_type='mea')
    phonecalls_short_received_perc = p_tables.CDDetectionVariable(
        detection_variable_name='phonecalls_short_received_perc', base_unit='float', detection_variable_type='mea')
    physicalactivity_calories = p_tables.CDDetectionVariable(detection_variable_name='physicalactivity_calories',
                                                             base_unit='float', detection_variable_type='mea')
    physicalactivity_intense_time = p_tables.CDDetectionVariable(
        detection_variable_name='physicalactivity_intense_time',
        base_unit='integer', detection_variable_type='mea')
    physicalactivity_moderate_time = p_tables.CDDetectionVariable(
        detection_variable_name='physicalactivity_moderate_time', base_unit='integer', detection_variable_type='mea')
    physicalactivity_num = p_tables.CDDetectionVariable(detection_variable_name='physicalactivity_num',
                                                        base_unit='integer', detection_variable_type='mea')
    physicalactivity_soft_time = p_tables.CDDetectionVariable(detection_variable_name='physicalactivity_soft_time',
                                                              base_unit='integer', detection_variable_type='mea')
    publicpark_time = p_tables.CDDetectionVariable(detection_variable_name='publicpark_time', base_unit='integer',
                                                   detection_variable_type='mea')
    publicpark_visits_month = p_tables.CDDetectionVariable(detection_variable_name='publicpark_visits_month',
                                                           base_unit='integer', detection_variable_type='mea')
    publicpark_visits = p_tables.CDDetectionVariable(detection_variable_name='publicpark_visits', base_unit='integer',
                                                     detection_variable_type='mea')
    publictransport_distance_month = p_tables.CDDetectionVariable(
        detection_variable_name='publictransport_distance_month', base_unit='float', detection_variable_type='mea')
    publictransport_rides_month = p_tables.CDDetectionVariable(detection_variable_name='publictransport_rides_month',
                                                               base_unit='integer', detection_variable_type='mea')
    publictransport_time = p_tables.CDDetectionVariable(detection_variable_name='publictransport_time',
                                                        base_unit='integer', detection_variable_type='mea')
    restaurants_time = p_tables.CDDetectionVariable(detection_variable_name='restaurants_time', base_unit='integer',
                                                    detection_variable_type='mea')
    restaurants_visits_month = p_tables.CDDetectionVariable(detection_variable_name='restaurants_visits_month',
                                                            base_unit='integer', detection_variable_type='mea')
    restaurants_visits_week = p_tables.CDDetectionVariable(detection_variable_name='restaurants_visits_week',
                                                           base_unit='integer', detection_variable_type='mea')
    restroom_time = p_tables.CDDetectionVariable(detection_variable_name='restroom_time', base_unit='integer',
                                                 detection_variable_type='mea')
    restroom_visits = p_tables.CDDetectionVariable(detection_variable_name='restroom_visits', base_unit='integer',
                                                   detection_variable_type='mea')
    room_changes = p_tables.CDDetectionVariable(detection_variable_name='room_changes', base_unit='integer',
                                                detection_variable_type='mea')
    seniorcenter_long_visits = p_tables.CDDetectionVariable(detection_variable_name='seniorcenter_long_visits',
                                                            base_unit='integer', detection_variable_type='mea')
    seniorcenter_time = p_tables.CDDetectionVariable(detection_variable_name='seniorcenter_time', base_unit='integer',
                                                     detection_variable_type='mea')
    seniorcenter_time_out_perc = p_tables.CDDetectionVariable(detection_variable_name='seniorcenter_time_out_perc',
                                                              base_unit='float', detection_variable_type='mea')
    seniorcenter_visits = p_tables.CDDetectionVariable(detection_variable_name='seniorcenter_visits',
                                                       base_unit='integer', detection_variable_type='mea')
    seniorcenter_visits_month = p_tables.CDDetectionVariable(detection_variable_name='seniorcenter_visits_month',
                                                             base_unit='integer', detection_variable_type='mea')
    seniorcenter_visits_week = p_tables.CDDetectionVariable(detection_variable_name='seniorcenter_visits_week',
                                                            base_unit='integer', detection_variable_type='mea')
    shops_outdoor_time_perc = p_tables.CDDetectionVariable(detection_variable_name='shops_outdoor_time_perc',
                                                           base_unit='float', detection_variable_type='mea')
    shops_time = p_tables.CDDetectionVariable(detection_variable_name='shops_time', base_unit='integer',
                                              detection_variable_type='mea')
    shops_visits = p_tables.CDDetectionVariable(detection_variable_name='shops_visits', base_unit='integer',
                                                detection_variable_type='mea')
    shops_visits_week = p_tables.CDDetectionVariable(detection_variable_name='shops_visits_week', base_unit='integer',
                                                     detection_variable_type='mea')
    sleep_awake_time = p_tables.CDDetectionVariable(detection_variable_name='sleep_awake_time', base_unit='integer',
                                                    detection_variable_type='mea')
    sleep_deep_time = p_tables.CDDetectionVariable(detection_variable_name='sleep_deep_time', base_unit='integer',
                                                   detection_variable_type='mea')
    sleep_light_time = p_tables.CDDetectionVariable(detection_variable_name='sleep_light_time', base_unit='integer',
                                                    detection_variable_type='mea')
    sleep_rem_time = p_tables.CDDetectionVariable(detection_variable_name='sleep_rem_time', base_unit='integer',
                                                  detection_variable_type='mea')
    sleep_time = p_tables.CDDetectionVariable(detection_variable_name='sleep_time', base_unit='integer',
                                              detection_variable_type='mea')
    sleep_tosleep_time = p_tables.CDDetectionVariable(detection_variable_name='sleep_tosleep_time', base_unit='integer',
                                                      detection_variable_type='mea')
    sleep_wakeup_num = p_tables.CDDetectionVariable(detection_variable_name='sleep_wakeup_num', base_unit='integer',
                                                    detection_variable_type='mea')
    stairs_floor_changes_up = p_tables.CDDetectionVariable(detection_variable_name='stairs_floor_changes_up',
                                                           base_unit='integer', detection_variable_type='mea')
    still_time = p_tables.CDDetectionVariable(detection_variable_name='still_time', base_unit='integer',
                                              detection_variable_type='mea')
    supermarket_time = p_tables.CDDetectionVariable(detection_variable_name='supermarket_time', base_unit='integer',
                                                    detection_variable_type='mea')
    supermarket_time_perc = p_tables.CDDetectionVariable(detection_variable_name='supermarket_time_perc',
                                                         base_unit='float', detection_variable_type='mea')
    supermarket_visits = p_tables.CDDetectionVariable(detection_variable_name='supermarket_visits', base_unit='integer',
                                                      detection_variable_type='mea')
    supermarket_visits_week = p_tables.CDDetectionVariable(detection_variable_name='supermarket_visits_week',
                                                           base_unit='integer', detection_variable_type='mea')
    transport_time = p_tables.CDDetectionVariable(detection_variable_name='transport_time', base_unit='integer',
                                                  detection_variable_type='mea')
    tvwatching_time = p_tables.CDDetectionVariable(detection_variable_name='tvwatching_time', base_unit='integer',
                                                   detection_variable_type='mea')
    tvwatching_time_perc = p_tables.CDDetectionVariable(detection_variable_name='tvwatching_time_perc',
                                                        base_unit='float', detection_variable_type='mea')
    visitors_week = p_tables.CDDetectionVariable(detection_variable_name='visitors_week', base_unit='integer',
                                                 detection_variable_type='mea')
    visits_payed_week = p_tables.CDDetectionVariable(detection_variable_name='visits_payed_week', base_unit='integer',
                                                     detection_variable_type='mea')
    visits_received_week = p_tables.CDDetectionVariable(detection_variable_name='visits_received_week',
                                                        base_unit='integer', detection_variable_type='mea')
    walk_distance = p_tables.CDDetectionVariable(detection_variable_name='walk_distance', base_unit='integer',
                                                 detection_variable_type='mea')
    walk_distance_outdoor = p_tables.CDDetectionVariable(detection_variable_name='walk_distance_outdoor',
                                                         base_unit='integer', detection_variable_type='mea')
    walk_distance_outdoor_fast_perc = p_tables.CDDetectionVariable(
        detection_variable_name='walk_distance_outdoor_fast_perc', base_unit='float', detection_variable_type='mea')
    walk_distance_outdoor_slow_perc = p_tables.CDDetectionVariable(
        detection_variable_name='walk_distance_outdoor_slow_perc', base_unit='float', detection_variable_type='mea')
    walk_speed_outdoor = p_tables.CDDetectionVariable(detection_variable_name='walk_speed_outdoor', base_unit='float',
                                                      detection_variable_type='mea')
    walk_steps = p_tables.CDDetectionVariable(detection_variable_name='walk_steps', base_unit='integer',
                                              detection_variable_type='mea')
    walk_steps_outdoor = p_tables.CDDetectionVariable(detection_variable_name='walk_steps_outdoor', base_unit='integer',
                                                      detection_variable_type='mea')
    walk_time_outdoor = p_tables.CDDetectionVariable(detection_variable_name='walk_time_outdoor', base_unit='integer',
                                                     detection_variable_type='mea')
    washingmachine_sessions = p_tables.CDDetectionVariable(detection_variable_name='washingmachine_sessions',
                                                           base_unit='integer', detection_variable_type='mea')
    weakness = p_tables.CDDetectionVariable(detection_variable_name='weakness', base_unit='float',
                                            detection_variable_type='mea')
    weight = p_tables.CDDetectionVariable(detection_variable_name='weight', base_unit='float',
                                          detection_variable_type='mea')

    # Adding measures in the list
    list_of_measures.extend([appetite, bathroom_time, bathroom_visits, bedroom_time, bedroom_visits, cinema_time,
                             cinema_visits, cinema_visits_month, culturepoi_visits_month,
                             culturepoi_visits_time_perc_month, exhaustion, falls_month, foodcourt_time,
                             foodcourt_visits_month, foodcourt_visits_week, gp_time_month, gp_visits_month, heart_rate,
                             home_time, kitchen_time, kitchen_visits, livingroom_time, livingroom_visits, meals_num,
                             memory, othersocial_long_visits, othersocial_time, othersocial_time_out_perc,
                             othersocial_visits, outdoor_num, outdoor_time, pain, perceived_temperature, pharmacy_time,
                             pharmacy_visits_month, pharmacy_visits_week, pharmacy_visits, phonecalls_long_placed_perc,
                             phonecalls_short_received_perc, phonecalls_missed, phonecalls_placed,
                             phonecalls_placed_perc, phonecalls_received, phonecalls_received_perc,
                             phonecalls_short_placed_perc, phonecalls_short_received_perc, physicalactivity_calories,
                             physicalactivity_intense_time, physicalactivity_intense_time,
                             physicalactivity_moderate_time, physicalactivity_num, physicalactivity_soft_time,
                             publicpark_time, publicpark_visits_month, publicpark_visits,
                             publictransport_distance_month,
                             publictransport_rides_month, publictransport_time, restaurants_time,
                             restaurants_visits_month, restaurants_visits_week, restroom_time, restroom_visits,
                             room_changes, seniorcenter_long_visits, seniorcenter_time, seniorcenter_time_out_perc,
                             seniorcenter_visits, seniorcenter_visits_month, seniorcenter_visits_week,
                             shops_outdoor_time_perc, shops_time, shops_visits, shops_visits_week, sleep_awake_time,
                             sleep_deep_time, sleep_light_time, sleep_rem_time, sleep_time, sleep_tosleep_time,
                             sleep_wakeup_num, stairs_floor_changes_up, still_time, supermarket_time,
                             supermarket_time_perc, supermarket_visits, supermarket_visits_week, publictransport_time,
                             tvwatching_time, tvwatching_time_perc, visitors_week, visits_payed_week,
                             visits_received_week, walk_distance, walk_distance_outdoor,
                             walk_distance_outdoor_fast_perc, walk_distance_outdoor_slow_perc, walk_speed_outdoor,
                             walk_steps, walk_steps_outdoor, walk_time_outdoor, washingmachine_sessions,
                             weakness, weight, phonecalls_long_received_perc, transport_time])

    # Insert data, pending action
    p_orm.insert_all(list_of_measures)
    # Commit changes
    p_orm.commit()


def create_actions(p_tables, p_orm):
    """
    This method create the needed table to store the list of base actions in database

    :param p_tables: The tables instance containing available tables
    :param p_orm: The orm connection to the target schema
    :return: 
    """
    list_of_actions = []
    # Defining city LEAS
    poi_enter = p_tables.CDAction(action_name='poi_enter',
                                  action_description="The user entered a relevant Point of Interest (POI) in the city "
                                                     "or in the home. The identification and type of the considered POI "
                                                     "is specified in the location property of the CDF")
    poi_in = p_tables.CDAction(action_name='poi_in',
                               action_description="The user is currently at a relevant Point of Interest in the city or"
                                                  " in the home. The identification and type of the considered POI is "
                                                  "specified in the location property of the CDF")
    poi_exit = p_tables.CDAction(action_name='poi_exit',
                                 action_description="The user left a relevant Point of Interest in the city or in the "
                                                    "home. The identification and type of the considered POI is "
                                                    "specified in the location property of the CDF")

    transport_enter = p_tables.CDAction(action_name='transport_enter',
                                        action_description="The user entered a transportation mean. The identification "
                                                           "and type of the transportation mean is specified in the "
                                                           "location property of the CDF")
    transport_exit = p_tables.CDAction(action_name='transport_exit',
                                       action_description="The user left a transportation mean. The identification "
                                                          "and type of the transportation mean is specified in the "
                                                          "location property of the CDF")
    # Defining home LEAS
    room_enter = p_tables.CDAction(action_name='room_enter',
                                   action_description="The user entered a relevant room in her/his home. The "
                                                      "identification and type of the room is specified in the "
                                                      "location property of the CDF")
    room_in = p_tables.CDAction(action_name='room_in',
                                action_description="The user is currently at a relevant room in her/his home. The "
                                                   "identification and type of the room is specified in the location "
                                                   "property of the CDF")
    room_exit = p_tables.CDAction(action_name='room_exit',
                                  action_description="The user left a relevant room in her/his home. The "
                                                     "identification and type of the room is specified in the "
                                                     "location property of the CDF")
    appliance_on = p_tables.CDAction(action_name='appliance_on',
                                     action_description="The user switched a relevant home appliance on")
    appliance_off = p_tables.CDAction(action_name='appliance_off',
                                      action_description="The user switched a relevant home appliance off")

    furniture_open = p_tables.CDAction(action_name='furniture_open',
                                       action_description="The user opened a piece of furniture")
    furniture_closed = p_tables.CDAction(action_name='furniture_closed',
                                         action_description="The user closed a piece of furniture")
    ambient_report = p_tables.CDAction(action_name='ambient_report',
                                       action_description="Report on current ambient conditions in the user’s "
                                                          "surroundings")
    # Defining Person LEAS
    body_state_start = p_tables.CDAction(action_name='body_state_start',
                                         action_description="The user entered a relevant body state")
    body_state_in = p_tables.CDAction(action_name='body_state_in',
                                      action_description="The user is currently in a relevant body state. Relevant, "
                                                         "current information about the state are reported")
    body_state_stop = p_tables.CDAction(action_name='body_state_stop',
                                        action_description="The user exited a relevant body state")
    fall_detect = p_tables.CDAction(action_name='fall_detect',
                                    action_description="The user fell")
    phone_in_start = p_tables.CDAction(action_name='phone_in_start',
                                       action_description="The user answered an incoming phone call")
    phone_in_stop = p_tables.CDAction(action_name='phone_in_stop',
                                      action_description="The user hung up an incoming phone call")
    phone_in_missed = p_tables.CDAction(action_name='phone_in_missed',
                                        action_description="The user missed an incoming phone call")
    phone_out_start = p_tables.CDAction(action_name='phone_out_start',
                                        action_description="The user placed an outbound phone call")
    phone_out_stop = p_tables.CDAction(action_name='phone_out_stop',
                                       action_description="The user hung up an outbound phone call")
    visit_start = p_tables.CDAction(action_name='visit_start',
                                    action_description="The user starts a visit (received or payed)")
    visit_stop = p_tables.CDAction(action_name='visit_stop',
                                   action_description="The user ends a visit (received or payed)")

    # Filling the list
    list_of_actions.extend([poi_enter, poi_in, poi_exit, transport_enter, transport_exit, room_enter, room_in,
                            room_exit, appliance_on, appliance_off, furniture_open, furniture_closed, ambient_report,
                            body_state_start, body_state_in, body_state_stop, fall_detect, phone_in_start,
                            phone_in_stop,
                            phone_in_missed, phone_out_start, phone_out_stop, visit_start, visit_stop])
    # Insert data, pending action
    p_orm.insert_all(list_of_actions)
    # Commit changes
    p_orm.commit()
