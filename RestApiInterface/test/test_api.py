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


class FlaskTestCase(unittest.TestCase):
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

    def test_get_my_info(self):
        """Test if the get my info is returning user-agent information"""
        response = self.app.get('/api/0.1/get_my_info')
        assert "ip" in response.data             # If response data cotnains the IP string, it is working well

    ###################################################
    ########   POST Tests
    ###################################################

    def test_no_header(self):
        """ Test status code 401: when there isn't any content_type header and we are not authorized"""
        response = self.app.get('/api/0.1/login', data="Not a json data format, and not header type json",
                                follow_redirects=True, headers=None)
        self.assertEqual(response.status_code, 401)

    def test_invalid_json(self):
        """ Test status code 400: when header is correct but data is not correct"""
        response = self.app.post('/api/0.1/add_action',
                                 data="Not a json data format, but we have good content type header",
                                 content_type='application/json',
                                 headers=self.headers_good,
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 400)

    def test_invalid_login(self):
        """ Test if the user sends no header with the credentials """
        response = self.app.get('/api/0.1/login', content_type='application/json', follow_redirects=True)
        self.assertEqual(response.status_code, 401)

    def test_wrong_login(self):
        """ Test if the system return error 401 unauthorized"""
        response = self.app.get('/api/0.1/login',
                                data=json.dumps(dict(username='admin', password='admin12')),
                                content_type='application/json', follow_redirects=True, headers=self.headers_bad)
        self.assertEqual(response.status_code, 401)

    def test_ok_login(self):
        """ Test if the system returns 200 code login ok"""
        response = self.app.get('/api/0.1/login', content_type='application/json', follow_redirects=True,
                                headers=self.headers_good)
        self.assertEqual(response.status_code, 200)

    ### Add_action

    # TODO add action related tests




    """
    def test_basic_search(self):
        # Test if we got any results
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
      """

    """
    def test_search_limit(self):
        # Test if a search has a limit
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

    """

    """
    def test_search_offset(self):
        # Test if a search has a offset
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
    """



if __name__ == '__main__':
    unittest.main()
