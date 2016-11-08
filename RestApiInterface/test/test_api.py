# -*- coding: utf-8 -*-

"""
This file emulates an user to test api.py file.

This file is divided into the following TESTS:

-> Get Test:        Containing various tests of GET calls.
-> Post Test:       Containing various test of POST calls.
-> Internal test:   Containing various test of internal functions (checks json by using JSON SCHEMA)

"""

import json
import unittest
from jsonschema import ValidationError
from testfixtures import should_raise

from packFlask.api import app
from packFlask import api
from packORM import post_orm
from packUtils.utilities import Utilities


__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2016, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"


class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        # Creates a testomg secret key for session management.
        app.config['SECRET_KEY'] = 'sekrit!'
        app.config['TESTING'] = True
        # app.config['SESSION_COOKIE_DOMAIN'] = None
        self.app = app.test_client()
        self.database = post_orm.PostgORM()

    def tearDown(self):
        # Closing database
        self.database.close()

    ###################################################
    ########   GET Tests
    ###################################################

    def test_good_api(self):
        """ Test if application wams about api level"""
        response = self.app.get('/api/0.9')
        assert "You have entered an invalid api version" in response.data

    def test_index_redirect(self):
        """ Test index redirect"""
        response = self.app.get('/', follow_redirects=True)
        assert "<h1>Welcome to City4Age Rest A" in response.data

    def test_api_redirect(self):
        """ Test Api redirect"""
        response = self.app.get('/api', follow_redirects=True)
        assert "<h1>Welcome to City4Age Rest A" in response.data

    ###################################################
    ########   POST Tests
    ###################################################

    def test_no_header(self):
        """ Test status code 400: when there isn't any content_type header"""
        response = self.app.post('/api/0.1/login',
                                 data="Not a json data format, and not header type json",
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 400)

    def test_invalid_json(self):
        """ Test status code 400: when header is correct but data is not correct"""
        response = self.app.post('/api/0.1/login',
                                 data="Not a json data format, but we have good content type header",
                                 content_type='application/json',
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 400)

    def test_invalid_login(self):
        """ Test if the user send invalid JSON fields for login into the system """
        response = self.app.post('/api/0.1/login',
                                 data=json.dumps(dict(username='admin', password11='admin')),
                                 content_type='application/json',
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 500)

    def test_wrong_login(self):
        """ Test if the system return error 401 unauthorized"""
        response = self.app.post('/api/0.1/login',
                                 data=json.dumps(dict(username='admin', password='admin12')),
                                 content_type='application/json',
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 401)

    def test_ok_login(self):
        """ Test if the system returns 200 code login ok"""
        response = self.app.post('/api/0.1/login',
                                 data=json.dumps(dict(username='admin', password='admin')),
                                 content_type='application/json',
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_basic_search(self):
        """ Test if we got any results """
        with self.app as c:
            with c.session_transaction() as sess:
                database = post_orm.PostgORM()
                sess['token'] = database.verify_user_login({
                    'username': 'admin', 'password': 'admin'}, app)

        response = c.post('/api/0.1/search',
                          data=json.dumps(dict(table='user_in_system',
                                               criteria={'username': 'admin'},
                                               limit=100,
                                               order_by='desc'
                                               )),
                          content_type='application/json',
                          follow_redirects=True)

        assert "No data found with this filters" not in response.data and response.status_code == 200

    def test_search_limit(self):
        """ Test if a search has a limit"""
        with self.app as c:
            with c.session_transaction() as sess:
                database = post_orm.PostgORM()
                sess['token'] = database.verify_user_login({
                    'username': 'admin', 'password': 'admin'}, app)
        response = c.post('/api/0.1/search',
                          data=json.dumps(dict(table='user_in_system',
                                               criteria={'username': 'admin'},
                                               limit=1,
                                               order_by='desc'
                                               )),
                          content_type='application/json',
                          follow_redirects=True)

        # todo we need to add more data
        # If the size of the response is equal 1 them OK
        response_size = len(list(response.response))
        assert response_size == 1 and response.status_code == 200 and \
               'No data found with this filters' not in response.data

    def test_search_offset(self):
        """ Test if a search has a offset"""
        with self.app as c:
            with c.session_transaction() as sess:
                database = post_orm.PostgORM()
                sess['token'] = database.verify_user_login({
                    'username': 'admin', 'password': 'admin'}, app)
        response = c.post('/api/0.1/search',
                          data=json.dumps(dict(table='user_in_system',
                                               criteria={'username': 'admin'},
                                               limit=100,
                                               order_by='desc',
                                               offset=1,
                                               )),
                          content_type='application/json',
                          follow_redirects=True)

        assert response.data.count('ruben') == 0 and response.status_code == 200

    ###################################################
    ########   INTERNAl Tests
    ###################################################

    def test_check_add_action_data(self):
        """ Test if action data check is working well"""
        json_example_action = {
            "action": "eu:c4a:usermotility:enter_bus",
            "location": "it:puglia:lecce:bus:39",
            "payload": {
                "user": "eu:c4a:pilot:madrid:user:12346",
                "position": "urn:ogc:def:crs:EPSG:6.6:4326"
            },
            "timestamp": "2014-05-20 07:08:41.22222",
            "rating": 0.1,
            "extra": {
                "pilot": "lecce"
            },
            "secret": "jwt_token"
        }

        json_example_action_list = [{
            "action": "eu:c4a:usermotility:enter_bus",
            "location": "it:puglia:lecce:bus:39",
            "payload": {
                "user": "eu:c4a:pilot:madrid:user:12346",
                "position": "urn:ogc:def:crs:EPSG:6.6:4326"
            },
            "timestamp": "2014-05-20 07:08:41.22222",
            "rating": 0.1,
            "extra": {
                "pilot": "lecce"
            },
            "secret": "jwt_token"
        }]

        self.assertTrue(Utilities.check_add_action_data(json_example_action) and
                        Utilities.check_add_action_data(json_example_action_list))

    def test_check_add_activity_data(self):
        """ Test if activity data check is working well"""
        json_example_activity = {
            "activity_name": "kitchenActivity",
            "activity_start_date": "2014-05-20 06:08:41.22222",
            "activity_end_date": "2014-05-20 07:08:41.22222",
            "since": "2014-05-20 01:08:41.22222",
            "house_number": 0,
            "location": {
                "name": "it:puglia:lecce:bus:39",
                "indoor": False
            },
            "pilot": "lecce"
        }

        json_example_activity_list = [{
            "activity_name": "kitchenActivity",
            "activity_start_date": "2014-05-20 06:08:41.22222",
            "activity_end_date": "2014-05-20 07:08:41.22222",
            "since": "2014-05-20 01:08:41.22222",
            "house_number": 0,
            "location": {
                "name": "it:puglia:lecce:bus:39",
                "indoor": False
            },
            "pilot": "lecce"
        }]

        self.assertTrue(Utilities.check_add_activity_data(json_example_activity) and
                        Utilities.check_add_activity_data(json_example_activity_list))

    def test_check_add_new_user(self):
        """ Test if the add new user check is working well"""
        json_example_user = {
            "username": "rmulero",
            "password": "heyPassWord1212323@@@#@3!!",
            "type": "admin"
        }

        json_example_user_list = [{
            "username": "rmulero",
            "password": "heyPassWord1212323@@@#@3!!",
            "type": "admin"
        }]

        self.assertTrue(Utilities.check_add_new_user(json_example_user) and
                        Utilities.check_add_new_user(json_example_user_list))

    def test_check_search(self):
        """ Test if search check is working well"""
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


if __name__ == '__main__':
    unittest.main()
