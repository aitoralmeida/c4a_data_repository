# -*- coding: utf-8 -*-

import json
import unittest

from src.packFlask.api import app


class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        # Creates a testomg secret key for session management.
        app.config['SECRET_KEY'] = 'sekrit!'
        app.config['TESTING'] = True
        # app.config['SESSION_COOKIE_DOMAIN'] = None
        self.app = app.test_client()

    ######## GET TESTS
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

    ####### POST TEST
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

    # todo see another way to obtain user session login
    def test_basic_search(self):
        """ Test if we got any results """
        with self.app as c:
            with c.session_transaction() as sess:
                sess['logged_in'] = True

        # ?
        response = self.app.post('/api/0.1/search',
                                 data=json.dumps(dict(username='admin')),
                                 content_type='application/json',
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_search_limit(self):
        """ Test if a search has a limit"""
        with self.app as c:
            with c.session_transaction() as sess:
                sess['logged_in'] = True
        response = self.app.post('/api/0.1/search',
                                 data=json.dumps(dict(username='Ruben', limit=2)),
                                 content_type='application/json',
                                 follow_redirects=True)

        # See an assert to 2 items only (count(


    def test_search_offset(self):
        """ Test if a search has a offset"""
        with self.app as c:
            with c.session_transaction() as sess:
                sess['logged_in'] = True
        response = self.app.post('/api/0.1/search',
                                 data=json.dumps(dict(username='Ruben', offset=3)),
                                 content_type='application/json',
                                 follow_redirects=True)

        # See assert for only one element if we use offset = 3 (4 result in DB).


if __name__ == '__main__':
    unittest.main()
