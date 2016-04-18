# -*- coding: utf-8 -*-

import json
import unittest

from src.packFlask.api import app

#todo we need to change this test to final form when we have defined DB structure

class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    ################################################ POST TEST
    def test_no_header(self):
        """Test status code 400: when there isn't any content_type header"""
        response = self.app.post('/add_action',
                                 data="Not a json data format, and not header type json",
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 400)

    def test_invalid_json(self):
        """Test status code 400: when header is correct but data is not correct"""
        response = self.app.post('/add_action',
                                 data="Not a json data format, but we have good content type header",
                                 content_type='application/json',
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 400)

    def test_ko_json_data(self):
        """Test insert data ko: when all data is in JSON format but is not correct with the current database"""
        response = self.app.post('/add_action', data=json.dumps(dict(loc='Chicago')),
                                 content_type='application/json',
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 500)

    def test_empty_json_data(self):
        """Test insert empty data: For the moment we can do this"""
        # todo allow to insert empty data?
        response = self.app.post('/add_action', data=json.dumps(dict(location=None)),
                                 content_type='application/json',
                                 follow_redirects=True)

        assert "Data stored in DB" in response.data

    def test_ok_json_data(self):
        """Test insert data ok: when all data is correct and DB returns an stored ok"""
        response = self.app.post('/add_action', data=json.dumps(dict(location='Chicago')),
                                 content_type='application/json',
                                 follow_redirects=True)
        assert "Data stored in DB" in response.data

    ################################################ GET TEST
    def test_get_data(self):
        """Test get all data call: If all is ok we have status_code 200 OK"""
        rv = self.app.get('add_action', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)

if __name__ == '__main__':
    unittest.main()
