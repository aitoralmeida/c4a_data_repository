# -*- coding: utf-8 -*-


"""
This file is intented to use to test the utilities class. The primary idea is to know if the different implemented
utility checks are working as intented and are validating the new entered data by the user. 

"""

import json
import unittest
from base64 import b64encode

from packControllers import post_orm, ar_post_orm, sr_post_orm
from packFlask.api import app
from packUtils.utilities import Utilities


__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2016, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"


class UtilitiesTestCase(unittest.TestCase):
    def setUp(self):
        # Creates a testomg secret key for session management.
        app.config['SECRET_KEY'] = 'sekrit!'
        app.config['TESTING'] = True
        # app.config['SESSION_COOKIE_DOMAIN'] = None
        self.app = app.test_client()
        self.ar_database = ar_post_orm.ARPostORM()
        self.sr_database = sr_post_orm.SRPostORM()
        self.headers_good = {
            'Authorization': 'Basic ' + b64encode("{0}:{1}".format('admin', 'admin'))
        }
        self.headers_bad = {
            'Authorization': 'Basic ' + b64encode("{0}:{1}".format('admin', 'admun'))
        }

    def tearDown(self):
        # Closing database
        self.ar_database.close()
        self.sr_database.close()

    def test_check_add_action_data(self):
        """ Test if action data check is working well"""
        json_example_action = {
             "action": "eu:c4a:usermotility:still_start",
             "location": "it:puglia:lecce:address:roomID",
             "payload": {
                 "user": "eu:c4a:pilot:lecce:user:12345",
                 "instanceID": "2"
             },
             "timestamp": "2016-05-19 07:08:41.013329",
             "rating": 0.4,
             "extra": {
                 "pilot": "lecce"
             },
             "secret": "jwt_token"
        }

        json_example_action_list = [
            {
                "action": "eu:c4a:usermotility:still_start",
                "location": "it:puglia:lecce:address:roomID",
                "payload": {
                    "user": "eu:c4a:pilot:lecce:user:12345",
                    "instanceID": "2"
                },
                "timestamp": "2016-05-19 07:08:41.013329",
                "rating": 0.4,
                "extra": {
                    "pilot": "lecce"
                },
                "secret": "jwt_token"
            },
            {
                "action": "eu:c4a:usermotility:walking_start",
                "location": {
                    "lat": "41",
                    "long": "18"
                },
                "payload": {
                    "user": "eu:c4a:pilot:lecce:user:12345",
                    "instanceID": "2",
                    "speed": "3.1",
                    "info_id": "4"
                },
                "timestamp": "2016-05-19 07:08:41.013329",
                "rating": 0.4,
                "extra": {
                    "pilot": "lecce"
                },
                "secret": "jwt_token"
            }
        ]

        self.assertTrue(Utilities.check_add_action_data(json_example_action) and
                        Utilities.check_add_action_data(json_example_action_list))

    def test_check_add_activity_data(self):
        """ Test if activity data check is working well"""
        json_example_activity = {
                "activity_name": "LeaveShop",
                "activity_description": "The user leaves one shop",
                "instrumental": False,
                "house_number": 23,
                "indoor": True,
                "location": "eu:c4a:Shop:40",
                "pilot": "MAD"
            }

        json_example_activity_list = [
            {
                "activity_name": "LeaveHouse",
                "activity_description": "Some description of the activity",
                "instrumental": True,
                "house_number": 0,
                "indoor": False,
                "location": "eu:c4a:Bus:39",
                "pilot": "LCC"
            },
            {
                "activity_name": "Take breakfast",
                "activity_description": "The user is taking breakfast at this moment"
            },
            {
                "activity_name": "EnterHouse"
            }
        ]

        self.assertTrue(Utilities.check_add_activity_data(self.ar_database, json_example_activity)[0] and
                        Utilities.check_add_activity_data(self.ar_database, json_example_activity_list)[0])

    def test_check_add_new_user(self):
        # Test if the add new user check is working well
        json_example_user = {
                "username": "andrew",
                "password": "thereissomethinglikemypassword1232",
                "valid_from": "2014-05-20T07:08:41.013+03:00",
                "valid_to": "2018-05-20T07:08:41.013+03:00",
                "user": "eu:c4a:user:8974587",
                "roletype": "administrator",
                "pilot": "ath"
        }

        json_example_user_list = [

                {
                    "username": "reind",
                    "password": "12334SESDAS",
                    "valid_from": "2014-05-20T07:08:41.013+03:00",
                    "valid_to": "2018-05-20T07:08:41.013+03:00",
                    "user": "eu:c4a:user:14526998",
                    "roletype": "care_giver",
                    "pilot": "ath"
                },

                {
                    "username": "denzel",
                    "password": "trustmeimauser",
                    "valid_from": "2014-05-20T07:08:41.013+03:00",
                    "valid_to": "2018-05-20T07:08:41.013+03:00",
                    "user": "eu:c4a:user:6598745987",
                    "roletype": "geriatrician",
                    "pilot": "MAD"
                }

        ]

        self.assertTrue(Utilities.check_add_new_user_data(self.ar_database, json_example_user)[0] and
                        Utilities.check_add_new_user_data(self.ar_database, json_example_user_list)[0])

    def test_check_add_new_care_receiver(self):
        # Test if the add care receiver checks are working
        json_example_care_receiver = {
                "pilot_user_source_id": "59874655415",
                "valid_from": "2017-04-03T10:02:09.029254+00:00",
                "username": "receiver1",
                "password": "thepassword"
            }

        json_example_care_receiver_list = [
            {
                "pilot_user_source_id": "xxXXX?????",
                "valid_from": "2015-04-03T10:02:09.029254+00:00",
                "username": "receiver1",
                "password": "thepassword"
            },

            {
                "pilot_user_source_id": "xxXXX?????",
                "valid_from": "2012-04-03T10:02:09.029254+00:00",
                "username": "receiver23",
                "password": "thepassworSSSd"
            }
        ]

        self.assertTrue(Utilities.check_add_care_receiver_data(self.ar_database, json_example_care_receiver)[0] and
                        Utilities.check_add_care_receiver_data(self.ar_database, json_example_care_receiver_list)[0])

    # TODO check utilities

    def test_check_add_measure_data(self):
        # Test if the add measure data checks are working
        json_example_add_measure = {
            "user": "eu:c4a:user:2598754",
            "pilot": "SIN",
            "interval_start": "2014-01-20T00:00:00.000+08:00",
            "duration": "DAY",
            "payload": {
                "WALK_STEPS": {"value": 1728},
                "SHOP_VISITS": {"value": 3, "data_source_type": ["sensors", "external_dataset"]},
                "PHONECALLS_PLACED_PERC": {"value": 21.23, "data_source_type": ["external_dataset"]}
            },
            "extra": {
                "pilot_specific_field": "some value"
            }
        }

        json_example_add_measure_list = [
            {
                "user": "eu:c4a:user:87456",
                "pilot": "MAD",
                "interval_start": "2014-01-20T00:00:00.000+08:00",
                "interval_end": "2015-01-20T00:00:00.000+08:00",
                "payload": {
                    "PHONECALLS_PLACED_PERC": {"value": 21.23, "data_source_type": ["external_dataset"]}
                },
                "extra": {
                    "pilot_specific_field": "ASDFGH"
                }
            },

            {
                "user": "eu:c4a:user:78432",
                "pilot": "SIN",
                "interval_start": "2014-01-20T00:00:00.000+08:00",
                "duration": "WK",
                "payload": {
                    "FURNITURE_CLOSED": {"value": 265, "data_source_type": ["sensors"]}
                },
                "extra": {
                    "pilot_specific_field": "TESTING"
                }
            }
        ]

        self.assertTrue(Utilities.check_add_measure_data(json_example_add_measure)[0] and
                        Utilities.check_add_measure_data(json_example_add_measure_list)[0])

    def check_add_eam_data(self):
        # Tests if add eam data checks are working

        json_example_add_eam = {
            "activity_name": "AnsweringPhone",
            "locations": ["Kitchen", "Office", "Bedroom"],
            "actions": ["KitchenPIR", "BedroomPIR"],
            "duration": 120,
            "start": [
                ["12:00", "12:05"],
                ["20:00", "20:10"]
            ]
        }

        json_example_add_eam_list = [
            {
                "activity_name": "PrepareBreakFast",
                "locations": ["Kitchen", "Bedroom"],
                "actions": ["KitchenPIR", "BedroomPIR"],
                "duration": 50,
                "start": [
                    ["10:00", "10:30"],
                    ["20:00", "20:10"]
                ]
            },
            {
                "activity_name": "MakeDinner",
                "locations": ["Kitchen"],
                "actions": ["KitchenPIR"],
                "duration": 60,
                "start": [
                    ["20:00", "20:30"],
                    ["22:00", "22:10"]
                ]
            }


        ]

        self.assertTrue(Utilities.check_add_measure_data(json_example_add_eam)[0] and
                        Utilities.check_add_measure_data(json_example_add_eam_list)[0])

    """
    def test_check_search(self):
         Test if search check is working well
        json_example_search = {
            'table': 'user_in_system',
            'criteria': {
                'col1': 'value',
                'col2': 'value'
            },
            ###### Optional parameters
            'limit': 2323,
            'offset': 2,
            'order_by': 'desc'
        }

        json_example_search_list = [{
            'table': 'user_in_system',
            'criteria': {
                'col1': 'value',
                'col2': 'value'
            },
            ###### Optional parameters
            'limit': 2323,
            'offset': 2,
            'order_by': 'desc'
        }]

        self.assertTrue(Utilities.check_search(self.database, json_example_search) and
                        Utilities.check_search(self.database, json_example_search_list))

    """

if __name__ == '__main__':
    unittest.main()
