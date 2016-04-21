# -*- coding: utf-8 -*-

import unittest
from testfixtures import should_raise
from sqlalchemy import create_engine, desc, inspect
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, DataError
from src.packORM import tables
from src.packORM import post_orm


__author__ = 'Rubén Mulero'
__copyright__ = "foo"   # we need?¿


class PostOrmTestCase(unittest.TestCase):
    def setUp(self):
        self.orm = post_orm.PostgORM()

    def tearDown(self):
        """ Close session """
        self.orm.close()

    def test_insert_one_user(self):
        """ Test pending insert  of one user works well"""
        data = tables.User(username='rmulero', password='rmulero', name='Ruben', lastname='Mil', age=23, genre='Male')
        self.orm.insert_one(data)
        ins = inspect(data)
        self.assertTrue(ins.pending)

    def test_insert_all_users(self):
        """ Test multiple pending insert of various users"""
        list_of_users = []
        res = False
        list_of_users.append(tables.User(username='rub', password='mul', name='Ruben', lastname='Mil', age=23, genre='Male'))
        list_of_users.append(tables.User(username='smith', password='1234', name='Smith', lastname='agent', age=98, genre='Male'))
        list_of_users.append(tables.User(username='neon22', password='white', name='Jonh', lastname='basw', age=87, genre='Male'))
        self.orm.insert_all(list_of_users)
        for user in list_of_users:
            ins = inspect(user)
            if ins.pending:
                res = True
            else:
                res = False
        self.assertTrue(res)


    def test_basic_query_not_found(self):
        """ Test if there isn't any result from DB """
        filters = {'username': 'pakorz', 'name': 'Pako'}
        t_class = tables.User
        q = self.orm.query(t_class, filters)
        # No matches found
        if q.count() == 0:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_basic_query_found(self):
        """ Test if there is a result"""
        filters = {'username': 'pako', 'name': 'Pako'}
        t_class = tables.User
        q = self.orm.query(t_class, filters)
        # No matches found
        if q.count() > 0 and q[0].name == 'Pako':
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_offset_query(self):
        """ Test if offset works well"""
        filters = {'username': 'rmulero', 'name': 'Ruben'}
        t_class = tables.User
        q = self.orm.query(t_class, filters, offset=3)
        # No matches found
        if q.count() > 0 and q[0].name == 'Ruben' and q[0].age == 90:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_limit_query(self):
        """ Test if a query is limited """

        filters = {'username': 'rmulero', 'name': 'Ruben'}
        t_class = tables.User
        q = self.orm.query(t_class, filters, limit=2)
        # No matches found
        if q.count() == 2:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_query_get(self):
        """ Test if providing an existing ID, our query have user information
            None --> Any user with this ID
            User Object --> User with this ID
        """
        user = self.orm.query_get(tables.User, p_id=3)
        self.assertTrue(user)

    def test_verify_user_login_ok(self):
        """ Test if an user login succesfully"""
        credentials = {'username': 'admin', 'password': 'admin'}
        res = self.orm.verify_user_login(credentials)
        self.assertTrue(res)

    def test_verify_user_login_ko_password(self):
        """ Test when users fails in login process """
        credentials = {'username': 'admin', 'password': 'adminnote'}
        res = self.orm.verify_user_login(credentials)
        self.assertFalse(res)

    def test_verify_user_login_ko_username(self):
        """ Test when users fails in login process """
        credentials = {'username': 'adminote', 'password': 'admin'}
        res = self.orm.verify_user_login(credentials)
        self.assertFalse(res)

    def test_verify_user_login_ko_empty_password(self):
        """ Test when users inserts an empty password"""
        credentials = {'username': 'adminote', 'password': ''}
        res = self.orm.verify_user_login(credentials)
        self.assertFalse(res)

    def test_verify_user_login_ko_empty_user(self):
        """ Test when users inserts an empty username"""
        credentials = {'username': '', 'password': 'admin'}
        res = self.orm.verify_user_login(credentials)
        self.assertFalse(res)

    def test_verify_user_login_ko_empty_user_password(self):
        """ Test when users inserts an empty username and password"""
        credentials = {'username': '', 'password': ''}
        res = self.orm.verify_user_login(credentials)
        self.assertFalse(res)

    def test_verify_user_login_ko_data(self):
        """ Test when user sends an invalid JSON"""
        credentials = {}
        res = self.orm.verify_user_login(credentials)
        self.assertFalse(res)


    # Raise ERRORs
    @should_raise(IntegrityError)
    def test_insert_an_existing_user(self):
        p_data = tables.User(id=6, username='rmulero', password='rmulero', name='Ruben', lastname='Mil', age=23, genre='Male')
        self.orm.session.add(p_data)
        self.orm.session.commit()

    @should_raise(AttributeError)
    def test_basic_query_bad_column(self):
        """ Test when the user make a query with bad columns"""
        filters = {'ages': 32}
        t_class = tables.User
        self.orm.query(t_class, filters)

    @should_raise(DataError)
    def test_bad_limit_query(self):
        """ Test if limit is negative """
        filters = {'username': 'rmulero', 'name': 'Ruben'}
        t_class = tables.User
        q = self.orm.query(t_class, filters, limit=-1)
        # No matches found
        if q.count() > 0:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    @should_raise(DataError)
    def test_bad_offset(self):
        """ Test if offset is negative"""
        filters = {'username': 'rmulero', 'name': 'Ruben'}
        t_class = tables.User
        q = self.orm.query(t_class, filters, offset=-1)
        # No matches found
        if q.count() > 0:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

    def test_bad_order_by(self):
        """ Test if orderby have a diferent arg"""
        filters = {'username': 'rmulero', 'name': 'Ruben'}
        t_class = tables.User
        q = self.orm.query(t_class, filters, order_by=-1)
        # No matches found
        if q.count() > 0:
            self.assertTrue(True)
        else:
            self.assertTrue(False)

if __name__ == '__main__':
    unittest.main()