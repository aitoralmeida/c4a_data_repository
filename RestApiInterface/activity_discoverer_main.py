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













# TODO --> Superhardcoded delete after finish



from src.packORM import ar_tables
from src.packControllers import ar_post_orm




"""
def insert_transformed(session, transformed_action, executed_action):


    # Self session to obtain ids
    session.flush()
    # Check if the count is only one
    if transformed_action:
        # We detect the popper transformed action in the
        executed_transformed_action = ar_tables.ExecutedTransformedAction(
            transformed_execution_datetime=executed_action.execution_datetime,
            transformed_acquisition_datetime=executed_action.acquisition_datetime,
            executed_action_id=executed_action.id,
            cd_transformed_action_id=transformed_action.id,
            user_in_role_id=executed_action.user_in_role_id)
        # Pending insert in DB
        session.insert_one(executed_transformed_action)
        # All done, res success

sess = ar_post_orm.ARPostORM()

list_of_leas = list()
start_time = '2016-01-02 06:08:41.013+02'
end_time = '2018-05-18 06:08:41.013+02'
# Dates are ok, we are going to extract needed LEAS from executed action table
query = sess.session.query(ar_tables.ExecutedAction).filter(
    ar_tables.ExecutedAction.execution_datetime.between(start_time, end_time),
    ar_tables.ExecutedAction.user_in_role_id == 11)

for q in query:
    # Transform the extract data into transofmred action
    cd_action = sess.session.query(ar_tables.CDAction).filter(ar_tables.CDAction.id == q.cd_action_id).first()
    location = sess.session.query(ar_tables.Location).filter(ar_tables.Location.id == q.location_id).first()
    transformed_action = None
    if q.cd_action_id == 5 and 'bus' in location.location_name:
        # Transformed action based on --> bus_exit
        transformed_action = sess.session.query(ar_tables.CDTransformedAction).filter_by(
            action_name=cd_action.action_name, location_type=location.location_name.split(':')[-2],
            appliance_type=None, furniture_type=None,
            state_type=None, calling_number=None)

    elif q.cd_action_id == 5 and 'car' in location.location_name:
        # Transofmred action based on --> car_exit
        transformed_action = sess.session.query(ar_tables.CDTransformedAction).filter_by(
            action_name=cd_action.action_name, location_type=location.location_name.split(':')[-2],
            appliance_type=None, furniture_type=None,
            state_type=None, calling_number=None)

    elif q.cd_action_id == 4 and 'bus' in location.location_name:
        # transformed action based on --> bus_enter
        transformed_action = sess.session.query(ar_tables.CDTransformedAction).filter_by(
            action_name=cd_action.action_name, location_type=location.location_name.split(':')[-2],
            appliance_type=None, furniture_type=None,
            state_type=None, calling_number=None)


    elif q.cd_action_id == 4 and 'car' in location.location_name:
        # transformed action based on --> car_enter
        transformed_action = sess.session.query(ar_tables.CDTransformedAction).filter_by(
            action_name=cd_action.action_name, location_type=location.location_name.split(':')[-2],
            appliance_type=None, furniture_type=None,
            state_type=None, calling_number=None)


    elif q.cd_action_id == 1 and 'home' in location.location_name:
        # transformed action based on --> home_enter
        transformed_action = sess.session.query(ar_tables.CDTransformedAction).filter_by(
            action_name=cd_action.action_name, location_type=location.location_name.split(':')[-2],
            appliance_type=None, furniture_type=None,
            state_type=None, calling_number=None)


    elif q.cd_action_id == 1 and 'familymemberhome' in location.location_name:
        # transformed action based on --> familynenberhome_enter
        transformed_action = sess.session.query(ar_tables.CDTransformedAction).filter_by(
            action_name=cd_action.action_name, location_type=location.location_name.split(':')[-2],
            appliance_type=None, furniture_type=None,
            state_type=None, calling_number=None)

    elif q.cd_action_id == 1 and 'supermarket' in location.location_name:
        # transformed action based on --> supermarket_exit

        transformed_action = sess.session.query(ar_tables.CDTransformedAction).filter_by(
            action_name=cd_action.action_name, location_type=location.location_name.split(':')[-2],
            appliance_type=None, furniture_type=None,
            state_type=None, calling_number=None)

    elif q.cd_action_id == 3 and 'home' in location.location_name:
        # transformed action based on --> home_exit

        transformed_action = sess.session.query(ar_tables.CDTransformedAction).filter_by(
            action_name=cd_action.action_name, location_type=location.location_name.split(':')[-2],
            appliance_type=None, furniture_type=None,
            state_type=None, calling_number=None)

    elif q.cd_action_id == 3 and 'familymemberhome' in location.location_name:
        # transformed action based on --> familynenberhome_exit

        transformed_action = sess.session.query(ar_tables.CDTransformedAction).filter_by(
            action_name=cd_action.action_name, location_type=location.location_name.split(':')[-2],
            appliance_type=None, furniture_type=None,
            state_type=None, calling_number=None)

    elif q.cd_action_id == 3 and 'supermarket' in location.location_name:
        # transformed action based on --> supermarket_exit
        transformed_action = sess.session.query(ar_tables.CDTransformedAction).filter_by(
            action_name=cd_action.action_name, location_type=location.location_name.split(':')[-2],
            appliance_type=None, furniture_type=None,
            state_type=None, calling_number=None)

    elif q.cd_action_id == 14:
        # transformed action based on --> walking_start

        transformed_action = sess.session.query(ar_tables.CDTransformedAction).filter_by(
            action_name=cd_action.action_name, location_type=None,
            appliance_type=None, furniture_type=None,
            state_type='walking', calling_number=None)

    elif q.cd_action_id == 15:
        # transformed action based on --> walking_stop
        transformed_action = sess.session.query(ar_tables.CDTransformedAction).filter_by(
            action_name=cd_action.action_name, location_type=None,
            appliance_type=None, furniture_type=None,
            state_type='walking', calling_number=None)

    elif q.cd_action_id == 16:
        # body_state_stop
        transformed_action = sess.session.query(ar_tables.CDTransformedAction).filter_by(
            action_name=cd_action.action_name, location_type=None,
            appliance_type=None, furniture_type=None,
            state_type='walking', calling_number=None)

    insert_transformed(sess, transformed_action.first(), q)


sess.commit()

"""

if __name__ == '__main__':
    ar = ActivityDiscoverer()
    # Extracting the user affected by EAMs
    list_user = ar.user_in_eam_extractor()
    # Process for each user
    for user in list_user:
        logging.debug("Starting activity recognition for the user: ", user)
        # Setting some time intervals
        start_date = '2016-01-02 06:08:41.013+02'
        end_date = '2018-05-18 06:08:41.013+02'
        # TODO uncomment this after finising your tests
        # end_date = arrow.utcnow()                         # current time
        # start_date = end_date.shift(weeks=-1)             # 1 week
        data = ar.lea_extractor(user, start_date, end_date)
        # After obtained the list of leas we are going to process it
        if len(data) > 0:
            # This user has LEA data stored in database with the given dates
            res = ar.execute_casas(data)
            if res:
                # Executing the HARSS algoritmh
                ar.execute_hars(p_user_in_role=user)
            else:
                raise Exception('The casas algoritmh is failing, check the logs')
