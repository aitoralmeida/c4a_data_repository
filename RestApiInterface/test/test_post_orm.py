# -*- coding: utf-8 -*-

import unittest
from testfixtures import should_raise
from sqlalchemy import create_engine, desc, inspect
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, DataError
from packORM import tables
from packORM import post_orm
from packFlask.api import app


__author__ = 'Rubén Mulero'
__copyright__ = "foo"   # we need?¿


class PostOrmTestCase(unittest.TestCase):
    def setUp(self):
        self.orm = post_orm.PostgORM()

    def tearDown(self):
        """ Close session """
        self.orm.close()


    ###################################################
    ########   Insert tests
    ###################################################

    def test_insert_one_user(self):
        """ Test pending insert  of one user works well"""
        data = tables.UserInSystem(username='rmulero', password='rmulero')
        self.orm.insert_one(data)
        ins = inspect(data)
        self.assertTrue(ins.pending)

    def test_insert_all_users(self):
        """ Test multiple pending insert of various users"""
        list_of_users = []
        res = False
        list_of_users.append(tables.UserInSystem(username='rub', password='mul'))
        list_of_users.append(tables.UserInSystem(username='smith', password='1234'))
        list_of_users.append(tables.UserInSystem(username='neon22', password='white'))
        self.orm.insert_all(list_of_users)
        for user in list_of_users:
            ins = inspect(user)
            if ins.pending:
                res = True
            else:
                res = False
        self.assertTrue(res)

    def test_insert_one_data(self):
        """ Test if defined data is inserted into DB

        For this test it is going to simulate and addition of new user.

        """
        list_of_dic_data = []
        user1 = {
            'username': 'rub',
            'password': 'mul',
            'type': 'caregiver'
        }
        # Adding user in system
        list_of_dic_data.append(user1)
        self.orm.add_new_user_in_system(list_of_dic_data)
        # check if exists.
        q = self.orm.query(tables.UserInSystem, {'username': 'rub'})
        self.assertTrue(q.count() > 0)

    ###################################################
    ########   Basic queries
    ###################################################

    def test_basic_query_not_found(self):
        """ Test if there isn't any result from DB """
        filters = {'username': 'pakorz'}
        t_class = tables.UserInSystem
        q = self.orm.query(t_class, filters)
        # No matches found
        self.assertTrue(q.count() == 0)

    def test_basic_query_found(self):
        """ Test if there is a result"""
        filters = {'username': 'admin'}
        t_class = tables.UserInSystem
        q = self.orm.query(t_class, filters)
        # No matches found
        self.assertTrue(q.count() > 0 and q[0].username == 'admin')



# Todo not working well this 3 tests

    def test_offset_query(self):
        """ Test if the offset is working well by giving some user in system"""
        filters = {'username': 'admin'}
        t_class = tables.UserInSystem
        q = self.orm.query(t_class, filters, offset=3)
        w = self.orm.query(t_class, filters, offset=0)
        # We know that there isn't 3 admins in system so with offset there isn't any results
        self.assertTrue(q.count() == 0 and w.count() == 1)


    def test_limit_query(self):
        """ Test if the limit is working well by giving some data """
        # We are going to insert 3 types of data in database
        list_of_dic_data = []
        user1 = {
            'username': 'elementaltester1',
            'password': 'sd029308sd02iah9dy302uoih',
            'type': 'caregiver'
        }
        user2 = {
            'username': 'elementaltester2',
            'password': '··$)E2390dajd3049',
            'type': 'caregiver'
        }
        user3 = {
            'username': 'elementaltester3',
            'password': '^d+sad2304820A$·aosidoawS',
            'type': 'caregiver'
        }
        # Adding user in system
        list_of_dic_data.append(user1)
        list_of_dic_data.append(user2)
        list_of_dic_data.append(user3)
        self.orm.add_new_user_in_system(list_of_dic_data)
        # Calling into DB
        filters = {'username': 'elementaltester'}
        q = self.orm.query(tables.UserInSystem, filters, limit=2)
        # If we receive two elements the tests is OK
        self.assertTrue(q.count() == 2)

    def test_query_get(self):
        """ Test if providing an existing ID, our query have user information
            None --> Any user with this ID
            User Object --> User with this ID
        """
        user = self.orm.query_get(tables.UserInSystem, p_id=1)
        self.assertTrue(user)



    ###################################################
    ########   Login Related Tests
    ###################################################

    def test_verify_user_login_ok(self):
        """ Test if an user login succesfully"""
        credentials = {'username': 'admin', 'password': 'admin'}
        res = self.orm.verify_user_login(credentials, app)
        self.assertTrue(res)

    def test_verify_user_login_ko_password(self):
        """ Test when users fails in login process """
        credentials = {'username': 'admin', 'password': 'adminnote'}
        res = self.orm.verify_user_login(credentials, app)
        self.assertFalse(res)

    def test_verify_user_login_ko_username(self):
        """ Test when users fails in login process """
        credentials = {'username': 'adminote', 'password': 'admin'}
        res = self.orm.verify_user_login(credentials, app)
        self.assertFalse(res)

    def test_verify_user_login_ko_empty_password(self):
        """ Test when users inserts an empty password"""
        credentials = {'username': 'adminote', 'password': ''}
        res = self.orm.verify_user_login(credentials, app)
        self.assertFalse(res)

    def test_verify_user_login_ko_empty_user(self):
        """ Test when users inserts an empty username"""
        credentials = {'username': '', 'password': 'admin'}
        res = self.orm.verify_user_login(credentials, app)
        self.assertFalse(res)

    def test_verify_user_login_ko_empty_user_password(self):
        """ Test when users inserts an empty username and password"""
        credentials = {'username': '', 'password': ''}
        res = self.orm.verify_user_login(credentials, app)
        self.assertFalse(res)

    def test_verify_user_login_ko_data(self):
        """ Test when user sends an invalid JSON"""
        credentials = {}
        res = self.orm.verify_user_login(credentials, app)
        self.assertFalse(res)


    ###################################################
    ########   List tables
    ###################################################

    def test_listing_ok_active_tables(self):
        """ Test if the method get_tables is listing well all tables"""
        res = self.orm.get_tables()
        self.assertTrue(len(res) > 0)


    ###################################################
    ########   Errors Test
    ###################################################

    @should_raise(IntegrityError)
    def test_insert_an_existing_user(self):
        p_data = tables.UserInSystem(id=3, username='admin', password='admin')
        self.orm.session.add(p_data)
        self.orm.session.commit()

    @should_raise(AttributeError)
    def test_basic_query_bad_column(self):
        """ Test when the user make a query with bad columns"""
        filters = {'ages': 32}
        t_class = tables.UserInSystem
        self.orm.query(t_class, filters)

    @should_raise(DataError)
    def test_bad_limit_query(self):
        """ Test if limit is negative """
        filters = {'username': 'admin'}
        t_class = tables.UserInSystem
        q = self.orm.query(t_class, filters, limit=-1)
        # No matches found
        self.assertTrue(q.count() > 0)

    @should_raise(DataError)
    def test_bad_offset(self):
        """ Test if offset is negative"""
        filters = {'username': 'admin'}
        t_class = tables.UserInSystem
        q = self.orm.query(t_class, filters, offset=-1)
        # No matches found
        self.assertTrue(q.count() > 0)

    def test_bad_order_by(self):
        """ Test if orderby have a diferent arg"""
        filters = {'username': 'admin'}
        t_class = tables.UserInSystem
        q = self.orm.query(t_class, filters, order_by=-1)
        # No matches found
        self.assertTrue(q.count() > 0)


if __name__ == '__main__':
    unittest.main()
