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
        # Detection variables
        create_detection_variables(sr_tables, sr_orm)
        logging.info("Created detection variables for Shared Repository schema")
        # TODO we need to be sure if this schema needs this datatype
        # Creating CDActivity information:
        create_actions(sr_tables, sr_orm)
        logging.info("Created Actions for Shared Repository schema")
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
    admin = p_tables.UserInRole(id=0,
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
    madrid = p_tables.Pilot(pilot_name='madrid', code='mad', population_size=3141991)
    lecce = p_tables.Pilot(pilot_name='lecce', code='lcc', population_size=89839)
    singapore = p_tables.Pilot(pilot_name='singapore', code='sin', population_size=5610000)
    montpellier = p_tables.Pilot(pilot_name='montpellier', code='mlp', population_size=268456)
    athens = p_tables.Pilot(pilot_name='athens', code='ath', population_size=3090508)
    birmingham = p_tables.Pilot(pilot_name='birmingham', code='bhx', population_size=1101360)
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


def create_measure(p_tables, p_orm):
    """
    This method inserts the measure dictionary with its different values and meanings

    :param p_tables: The tables instance containing available tables
    :param p_orm: The orm connection to the target schema
    :return: 
    """

    # TODO this method needs to be known
    list_of_measures = []

    #TODO INSERT INTO CD_DETECTION_VARIABLE -->

    walk_steps = p_tables.Measure(name='walk_steps',
                                  description='Number of steps done in the day')
    walk_steps_fast_perc = p_tables.Measure(name='walk_steps_fast_perc',
                                            description='Percentage of steps done at fast speed in the day.')
    walk_steps_medium_perc = p_tables.Measure(name='walk_steps_medium_perc',
                                              description='Percentage of steps done at medium speed the day.')
    walk_steps_slow_perc = p_tables.Measure(name='walk_steps_slow_perc',
                                            description='Percentage of steps done at slow speed in the day')
    walk_steps_indoor = p_tables.Measure(name='walk_steps_indoor',
                                         description='number of steps done indoor in the day')
    walk_steps_indoor_fast_perc = p_tables.Measure(name='walk_steps_indoor_fast_perc',
                                                   description='Percentage of steps done indoor at fast speed '
                                                               'in the day')
    walk_steps_indoor_medium_perc = p_tables.Measure(name='walk_steps_indoor_medium_perc',
                                                     description='Percentage of steps done indoor at medium speed '
                                                                 'in the day')
    walk_steps_indoor_slow_perc = p_tables.Measure(name='walk_steps_indoor_slow_perc',
                                                   description='Percentage of steps done indoor at slow speed '
                                                               'in the day')
    walk_steps_outdoor = p_tables.Measure(name='walk_steps_outdoor',
                                          description='Number of steps done outdoor in the day')
    walk_steps_outdoor_fast_perc = p_tables.Measure(name='walk_steps_outdoor_fast_perc',
                                                    description='Percentage of steps done outdoor at fast '
                                                                'speed in the day')
    walk_steps_outdoor_medium_perc = p_tables.Measure(name='walk_steps_outdoor_medium_perc',
                                                      description='Percentage of steps done outdoor at medium speed in the day')
    walk_steps_outdoor_slow_perc = p_tables.Measure(name='walk_steps_outdoor_slow_perc',
                                                    description='Percentage of steps done outdoor at slow speed in'
                                                                'the day')
    walk_distance = p_tables.Measure(name='walk_distance', description='Total distance in meters walked in the day')
    walk_distance_outdoor = p_tables.Measure(name='walk_distance_outdoor',
                                             description='total distance in meters walked '
                                                         'outdoor in the day')
    walk_distance_outdoor_fast_perc = p_tables.Measure(name='walk_distance_outdoor_fast_perc',
                                                       description='Percentage of distance walked outdoor at fast '
                                                                   'speed in the day on total distance walked outdoor')
    walk_distance_outdoor_slow_perc = p_tables.Measure(name='walk_distance_outdoor_slow_perc',
                                                       description='Percentage of distance walked outdoor at slow speed'
                                                                   ' in the day on total distance walked outdoor')
    walk_time_outdoor = p_tables.Measure(name='walk_time_outdoor',
                                         description='Time in seconds spend walking outdoor in the day')
    walk_speed_outdoor = p_tables.Measure(name='walk_speed_outdoor',
                                          description='Average outdoor walking speed in meters/seconds in the day')
    walk_elevation = p_tables.Measure(name='walk_elevation', description='Elevation in meters climbed in the day')
    stairs_floor_changes_up = p_tables.Measure(name='stairs_floor_changes_up',
                                               description='Number of fllor changes performed in the day by '
                                                           'climbing staris upwards')
    still_time = p_tables.Measure(name='still_time', description='Time in seconds spent in the still state in the day')
    physicalactivity_num = p_tables.Measure(name='physicalactivity_num', description='Number of physical activity '
                                                                                     'sessions attended in the day')
    physicalactivity_soft_time = p_tables.Measure(name='physicalactivity_soft_time',
                                                  description='Time in seconds spent in soft activities in the day')

    physicalactivity_moderate_time = p_tables.Measure(name='physicalactivity_soft_time',
                                                      description='Time in seconds spent in moderate activities '
                                                                  'in the day')
    physicalactivity_intense_time = p_tables.Measure(name='physicalactivity_intense_time',
                                                     description='Time in seconds spent in intense activities '
                                                                 'in the day')

    physicalactivity_calories = p_tables.Measure(name='physicalactivity_calories', description='Total calories in '
                                                                                               'kcal burned in the day')

    room_changes = p_tables.Measure(name='room_changes', description='Number of room changes in the day')
    bedroom_visits = p_tables.Measure(name='bedroom_visits', description='Number of bedroom entrances in the day.')
    bedroom_time = p_tables.Measure(name='bedroom_time', description='Time in seconds spent in bedroom in the day')
    bedroom_time_perc = p_tables.Measure(name='bedroom_time_perc', description='Percentage of time spent in bedroom '
                                                                               'in the day')
    livingroom_visits = p_tables.Measure(name='livingroom_visits',
                                         description='Number of living room entrances in the day')

    livingroom_time = p_tables.Measure(name='livingroom_time',
                                       description='Time in seconds spent in living room in the day')
    livingroom_time_perc = p_tables.Measure(name='livingroom_time_perc',
                                            description='Percentage of time spent in living room in the day')
    restroom_visits = p_tables.Measure(name='restroom_visits', description='Number of restroom entrances in the day')
    restroom_time = p_tables.Measure(name='restroom_time', description='Time in seconds spent in restroom in the day')
    restroom_time_perc = p_tables.Measure(name='restroom_time_perc', description='Percentage of time spent in '
                                                                                 'restroom in the day')
    kitchen_visits = p_tables.Measure(name='kitchen_visits', description='Number of kitchen entrances in the day')
    kitchen_time = p_tables.Measure(name='kitchen_time', description='Time in seconds spent in kitchen in the day')
    kitchen_time_perc = p_tables.Measure(name='kitchen_time_perc', description='Percentage of time spent in kitchen '
                                                                               'in the day')
    meals_num = p_tables.Measure(name='meals_num', description='Number of prepared meals delivered to the user '
                                                               'in the week')
    lunches_num = p_tables.Measure(name='lunches_num', description='Number of lunches')

    bathroom_visits = p_tables.Measure(name='bathroom_visits', description='Number of bathrooms entrances in a day')
    bathroom_time = p_tables.Measure(name='bathroom_time', description='Time in seconds spent in bathroom in the day')
    home_time = p_tables.Measure(name='home_time', description='Time in seconds spent at home in the day')
    outdoor_num = p_tables.Measure(name='outdoor_num', description='Total number of exits from home in the day')
    outdoor_time = p_tables.Measure(name='outdoor_time', description='Time in seconds spent outdoor in the day')
    indoor_outdoor_time_perc = p_tables.Measure(name='indoor_outdoor_time_perc',
                                                description='Percentage of time spent indoor with respect to time '
                                                            'spent outdoor in the day')
    washingmachine_sessions = p_tables.Measure(name='washingmachine_sessions',
                                               description='Washing machine usage sessions in the day')
    phonecalls_placed = p_tables.Measure(name='phonecalls_placed',
                                         description='Number of phone calls placed in the day')
    phonecalls_received = p_tables.Measure(name='phonecalls_received',
                                           description='Number of phone calls received in the day')
    phonecalls_missed = p_tables.Measure(name='phonecalls_missed',
                                         description='Number of phone calls missed in the day')
    phonecalls_placed_perc = p_tables.Measure(name='phonecalls_placed_perc',
                                              description='Percentage of phone calls placed on total phone calls '
                                                          'in the day')
    phonecalls_received_perc = p_tables.Measure(name='phonecalls_received_perc',
                                                description='Percentage of phone calls received on total phone calls '
                                                            'in a day')
    phonecalls_long_received_perc = p_tables.Measure(name='phonecalls_long_received_perc',
                                                     description='Percentage of long phone calls placed '
                                                                 'on total phone calls placed in the day.')
    phonecalls_short_received_perc = p_tables.Measure(name='phonecalls_short_received_perc',
                                                      description='Percentage of short phone calls placed on total '
                                                                  'phone calls placed in the day')

    phonecalls_long_placed_perc = p_tables.Measure(name='phonecalls_long_placed_perc',
                                                   description='Percentage of long phone calls placed on total phone '
                                                               'calls placed in a day')
    phonecalls_short_placed_perc = p_tables.Measure(name='phonecalls_short_placed_perc',
                                                    description='Percentage of short phone calls placed on total '
                                                                'phone calls placed in the day')

    shops_visit = p_tables.Measure(name='shops_visit', description='Number of visits to monitored shops ni the day')
    shops_visit_week = p_tables.Measure(name='shops_visit_week', description='Number of visits to monitored '
                                                                             'shops in the week')

    shops_time = p_tables.Measure(name='shops_time', description='Time in seconds spent in monitored shops in the day')
    shops_outdoor_time_perc = p_tables.Measure(name='shops_outdoor_time_perc',
                                               description='Percentage of time spent in monitored shops with respect '
                                                           'to time spent outdoor in the day')
    supermarket_visits = p_tables.Measure(name='supermarket_visits', description='Number of visits to monitored '
                                                                                 'supermarkets in the day')
    supermarket_visits_week = p_tables.Measure(name='supermarket_visits_week',
                                               description='Number of visits to monitored supermarkets in the week')
    supermarket_time = p_tables.Measure(name='supermarket_time', description='Time in seconds spent in monitored '
                                                                             'supermarkets in the day')
    supermarket_time_perc = p_tables.Measure(name='supermarket_time_perc',
                                             description='Percentage of time spent in monitored supermarkets on total '
                                                         'time spent in shops in the day')
    pharmacy_visits = p_tables.Measure(name='pharmacy_visits',
                                       description='Number of visits to monitored pharmacies in the day')
    pharmacy_visits_week = p_tables(name='pharmacy_visits_week',
                                    description='Number of visits to monitored pharmacies in the week')
    pharmacy_visits_month = p_tables.Measure(name='pharmacy_visits_month',
                                             description='Number of visits to monitored pharmacies in the month')
    pharmacy_time = p_tables.Measure(name='pharmacy_times',
                                     description='Time in seconds spent in monitored pharmacies in the day')

    publictransport_time = p_tables.Measure(name='publictransport_time', description='Time in seconds spent in public '
                                                                                     'transportation in the day')
    publictransport_rides_month = p_tables.Measure(name='publictransport_rides_month',
                                                   description='Number of times the user gets on the bus in a month')
    publictransport_distance_month = p_tables.Measure(name='publictransport_distance_month',
                                                      description='Distance in km travelled on the bus in a month')
    restaurants_visits_month = p_tables.Measure(name='restaurans_visits_month',
                                                description='number of visits to monitored restaurans in the month')
    cinema_visits_month = p_tables.Measure(name='cinema_visits_month',
                                           description='Number of visits to monitored cinema/theatres in the month')
    cinema_city_time_perc_month = p_tables.Measure(name='cinema_city_time_perc_month',
                                                   description='Percentage of time spent in monitored cinema/theatres '
                                                               'with respect to time spent outside home in the month')
    newshop_visits_month = p_tables.Measure(name='newshop_visits_month', description='Number of visits to monitored '
                                                                                     'newshops in the month')
    culturepoi_visits_month = p_tables.Measure(name='culturepoi_visits_month',
                                               description='Number of visits to monitored cultural places')
    culturepoi_city_time_perc_month = p_tables.Measure(name='culturepoi_city_time_perc_month',
                                                       description='Percentage of time spent in monitored cultural '
                                                                   'places with respect to time spent outside home '
                                                                   'in the month')
    tvwatching_time = p_tables.Measure(name='tvwatching_time', description='Time in seconds spent watching TV '
                                                                           'in the day')
    tvwatching_home_time_perc = p_tables.Measure(name='tvwatching_home_time_perc',
                                                 description='Percentage of time spent watching TV with respect to '
                                                             'time spent inside home in the day')
    seniorcenter_visits = p_tables.Measure(name='seniorcenter_visits', description='Number of visits to SeniorCenter '
                                                                                   'in the day')
    seniorcenter_long_visits = p_tables.Measure(name='seniorcenter_long_visits',
                                                description='Number of long visits to SeniorCenter in the day')
    seniorcenter_time = p_tables.Measure(name='seniorcenter_time',
                                         description='Time in seconds spent in SeniorCenter in the day')
    seniorcenter_time_perc = p_tables.Measure(name='seniorcenter_time_perc',
                                              description='Percentage of time spent in seniorCenter with respect '
                                                          'to total time in the day')
    seniorcenter_time_out_perc = p_tables.Measure(name='seniorcenter_time_out_perc',
                                                  description='Percentage of time spent in Seniorcenter with respect '
                                                              'to total time spent outside home in the day')
    othersocial_visits = p_tables.Measure(name='othersocial_visits',
                                          description='Number of visits to OtherSocialPlace in the day')
    othersocial_long_visits = p_tables.Measure(name='othersocial_long_visits',
                                               description='Number of long visits to OtherSocialPlace in the day')
    othersocial_time = p_tables.Measure(name='othersocial_time',
                                        description='Time in seconds spent in the OtherSocialPlace in the day')
    othersocial_time_perc = p_tables.Measure(name='othersocial_time_perc',
                                             description='Percentage of time spent in OtherSocialPlace with '
                                                         'respect to total time in the day')
    othersocial_time_out_perc = p_tables.Measure(name='othersocial_time_out_perc',
                                                 description='Percentage of time spent in OtherSocialPlace with '
                                                             'respect to total time spent outside home in the day')
    visits_received_week = p_tables.Measure(name='visits_received_week',
                                            description='Number of visits received in the week')
    visits_payed_week = p_tables.Measure(name='visits_payed_week', description='Number of visits payed in the week')
    visitors_week = p_tables.Measure(name='visitors_week', description='Number of visitors met in the week')
    visits_lenght_week = p_tables.Measure(name='visits_lenght_week',
                                          description='Total duration in seconds of visits in the week')
    falls_month = p_tables.Measure(name='falls_month', description='Number of falls detected in the month')
    sleep_time = p_tables.Measure(name='sleep_time', description='Total time in seconds spent sleeping in the day')
    sleep_light_time = p_tables.Measure(name='sleep_light_time',
                                        description='Total time in seconds spent in light sleeping in the day')
    sleep_deep_time = p_tables.Measure(name='sleep_deep_time',
                                       description='Total time in seconds spent in deep sleeping in the day')
    sleep_rem_time = p_tables.Measure(name='sleep_rem_time',
                                      description='Total time in seconds spent in REM sleeping in the day')
    sleep_awake_time = p_tables.Measure(name='sleep_rem_time',
                                        description='Total time in seconds spent awake while at rest in the day.')
    sleep_wakeup_num = p_tables.Measure(name='sleep_wakeup_num',
                                        description='Number of times the user woke up in the day.')
    sleep_tosleep_time = p_tables.Measure(name='sleep_tosleep_time',
                                          description='Total time in seconds the user spent falling asleep in the day.')
    sleep_towakeup_time = p_tables.Measure(name='sleep_towakeup_time',
                                            description='Total time in seconds the user spent waking up in the day.')
    bed_time = p_tables.Measure(name='bed_time', description='Total time in seconds spent in bed in the day.')
    good_sleep_time_perc = p_tables.Measure(name='good_sleep_time_perc',
                                            description='Percentage of good sleeping time on total sleeping time in the day.')
    gp_visits_month = p_tables.Measure(name='gp_visits_month', description='Number of visits to GP in the month.')
    gp_time_month = p_tables.Measure(name='gp_time_month', description='Time spent at GP’s practice in the month')
    healthplace_visits_month = p_tables.Measure(name='healthplace_visits_month',
                                                description='Number of visits to health related places in the month.')
    pain = p_tables.Measure(name='pain', description='Pain level reported in the day on a 1-5 scale')
    appetite = p_tables.Measure(name='appetite', description='Appetite reported in the day on a 1-5 scale')
    weight = p_tables.Measure(name='weight', description='User weight in kg sampled in the month.')
    weakness = p_tables.Measure(name='weakness', description='Grip strength in <units> sampled in the month.')
    exhaustion = p_tables.Measure(name='exhaustion', description='Exhaustion in <units> sampled in the month.')
    memory = p_tables.Measure(name='memory', description='Memory performance reported in the day, as numerical '
                                                         'indicator returned from the CANTAB system')
    gooddays_perc = p_tables.Measure(name='gooddays_perc', description='Percentage of good mood days in the week.')
    gooddays_num = p_tables.Measure(name='gooddays_num', description='Number of “pushed” good mood days in the week.')
    baddays_num = p_tables.Measure(name='baddays_num', description='Number of bad mood days in the week.')

    # Adding measures in the list
    list_of_measures.extend([walk_steps, walk_steps_fast_perc, walk_steps_medium_perc, walk_steps_slow_perc,
                             walk_steps_indoor, walk_steps_indoor_fast_perc, walk_steps_indoor_medium_perc,
                             walk_steps_indoor_slow_perc, walk_steps_outdoor, walk_steps_outdoor_fast_perc,
                             walk_steps_outdoor_medium_perc, walk_steps_outdoor_slow_perc, walk_distance,
                             walk_distance_outdoor, walk_distance_outdoor_fast_perc, walk_distance_outdoor_slow_perc,
                             walk_time_outdoor, walk_speed_outdoor, walk_elevation])

    list_of_measures.extend([stairs_floor_changes_up, still_time, physicalactivity_num, physicalactivity_soft_time,
                             physicalactivity_moderate_time, physicalactivity_intense_time, physicalactivity_calories])

    list_of_measures.extend([room_changes, bedroom_visits, bedroom_time, bedroom_time_perc, livingroom_visits,
                             livingroom_time, livingroom_time_perc, restroom_visits, restroom_time, restroom_time_perc,
                             kitchen_visits, kitchen_time, kitchen_time_perc, bathroom_visits, bathroom_time])

    list_of_measures.extend([meals_num, lunches_num, home_time, outdoor_num, outdoor_time, indoor_outdoor_time_perc,
                             washingmachine_sessions, phonecalls_placed, phonecalls_received, phonecalls_missed,
                             phonecalls_placed_perc, phonecalls_received_perc, phonecalls_long_received_perc,
                             phonecalls_short_received_perc, phonecalls_long_placed_perc, phonecalls_short_placed_perc])

    list_of_measures.extend([shops_visit, shops_visit_week, shops_time, shops_outdoor_time_perc, supermarket_visits,
                             supermarket_visits_week, supermarket_time, supermarket_time_perc, pharmacy_visits,
                             pharmacy_visits_week, pharmacy_visits_month, pharmacy_time])

    list_of_measures.extend([publictransport_time, publictransport_rides_month, publictransport_distance_month,
                             restaurants_visits_month, cinema_visits_month, cinema_city_time_perc_month,
                             newshop_visits_month, culturepoi_visits_month, culturepoi_city_time_perc_month,
                             tvwatching_time, tvwatching_home_time_perc])

    list_of_measures.extend([seniorcenter_visits, seniorcenter_long_visits, seniorcenter_time, seniorcenter_time_perc,
                             seniorcenter_time_out_perc, othersocial_visits, othersocial_long_visits, othersocial_time,
                             othersocial_time_perc, othersocial_time_out_perc, visits_received_week, visits_payed_week,
                             visitors_week, visits_lenght_week, falls_month])

    list_of_measures.extend([sleep_time, sleep_light_time, sleep_deep_time, sleep_rem_time, sleep_awake_time,
                             sleep_wakeup_num, sleep_tosleep_time, sleep_towakeup_time, bed_time, good_sleep_time_perc])

    list_of_measures.extend([gp_visits_month, gp_time_month, healthplace_visits_month, pain, appetite, weight, weakness,
                             exhaustion, memory, gooddays_perc, gooddays_num, baddays_num])

    # Insert data, pending action
    p_orm.insert_all(list_of_measures)


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
