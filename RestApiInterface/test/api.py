import unittest
from packFlask .api import app

class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_return_data(self):
        # If GET action return any kind of Python dict (empty or not
        rv = self.app.get('/add_action')
        assert "[{" in rv.data

    def test_add_data(self):
        rv = self.app.post('/add_action', data=dict(
                                            location='Sestao'
        ), follow_redirects=True)
        assert "Data stored in DB" in rv.data

if __name__ == '__main__':
    unittest.main()
