# -*- coding: utf-8 -*-

"""
This file is used to connect to the database using SQL Alchemy ORM

"""

import tables
import ConfigParser
from sqlalchemy import create_engine, desc
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker


__author__ = 'Rubén Mulero'
__copyright__ = "foo"   # we need?¿


# Database settings
config = ConfigParser.ConfigParser()
#config.readfp(open('./conf/rest_api.cfg'))
#todo change this later
config.readfp(open('../conf/rest_api.cfg'))


if 'database' in config.sections():
    # We have config file with data
    DATABASE = {
                    'drivername': config.get('database', 'drivername') or 'postgres',
                    'host': config.get('database', 'host') or 'localhost',
                    'port': config.get('database', 'port') or '5432',
                    'username': config.get('database', 'username') or 'postgres',
                    'password': config.get('database', 'password') or 'postgres',
                    'database': config.get('database', 'database') or 'postgres'
    }
else:
    # Any config file detected, load default settings.
    DATABASE = {
        'drivername': 'postgres',
        'host': 'localhost',
        'port': '5432',
        'username': 'postgres',
        'password': 'postgres',
        'database': 'postgres'
    }

class PostgORM(object):

    def __init__(self):
        # Make basic connection and setup declatarive
        self.engine = create_engine(URL(**DATABASE))
        try:
            session_mark = sessionmaker(bind=self.engine)   # Bind session engine Test connection
            session = session_mark()
            if session:
                print "Connection OK"
                self.session = session
        except OperationalError:
            print "Database arguments are invalid"

    def create_tables(self):
        """
        Create database tables
        :return:
        """
        return tables.create_tables(self.engine)

    def insert_one(self, p_data):
        """
        Insert one desired data

        :param p_data: Object from Tables
        :return: None
        """
        self.session.add(p_data)                  # Pending add (we can see new changes before commit)


    def insert_all(self, p_list_data):
        """
        Insert a list of Type of datas

        :param p_list_data: List of data
        :return: None
        """
        self.session.add_all(p_list_data)         # Multiple users, pending action

    def query(self, p_class, web_dict, limit=10, offset=0, order_by='asc'):
        """
        Makes a query to the desired table of databse and filter the result based on user choice.

        :param p_class:  Name of the table to query
        :param web_dict: A dict with colums and data to filter.
        :param limit: query limit (default is 10)
        :param offset: offset (default is 0)
        :param order_by: Set order of query (default is 'asc' on ID column)
        :return:
        """
        q = self.session.query(p_class)
        if q and web_dict and web_dict.items():
            # Filter based of the content of the dict
            for attr, value in web_dict.items():
                q = q.filter(getattr(p_class, attr).like("%%%s%%" % value))
        # ORder by
        if order_by is not 'asc':
            # Default order by id
            q = q.order_by(desc(p_class.id))
        # Limit and offset our query
        q = q.limit(limit)
        q = q.offset(offset)
        return q

    def query_get(self, p_class,  p_id):
        """
        Makes a querty to the desired Table of databased based on row ID

        :param p_class:  Name of the table to query
        :param p_id: id of the row
        :return: Object instance of the class or None
        """
        q = None
        res = self.session.query(p_class).get(p_id)
        if res:
            q = res
        return q

    def commit(self):
        """
        Commit all data and close the connection to DB.

        :return: None
        """
        if self.session.new:  # todo check if we need to know that session is new or not
            try:
                self.session.commit()
            except Exception:
                self.session.rollback()
        else:
            print "Session is not new. Check it"

    def close(self):
        """
        Force close the connecion of the actual session

        :return: None
        """
        if self.session:
            self.session.close()

    def verify_user_login(self, p_data):
        """
        This method check given user and password and create a new session for the current user.

        :param p_data: User and password
        :return: True or False if user/password are valid.
        """
        res = False
        if 'username' in p_data and 'password' in p_data:
            user_data = self.query(tables.User, {'username': p_data['username']})
            if user_data and user_data.count() == 1 and user_data[0].password == p_data['password'] \
                    and user_data[0].username == p_data['username']:
                print 'Access granted'
                res = True
            else:
                print "Wrong username/password"
        else:
            print "Rare exception"
        return res


    # def verify_user_login(self, p_data, app, expiration=600):
    #     """
    #     This method generates a new auth token to the user when username and password are OK
    #
    #     :param p_data: A Python dic with username and password.
    #     :param app: Flask application Object.
    #     :param expiration: Expiration time of the token.
    #
    #     :return: A string with token data or Error String.
    #     """
    #     if 'username' in p_data and 'password' in p_data and app:
    #         user_data = self.query(tables.User, p_data)
    #         if user_data and user_data[0]:
    #             # Login OK
    #             res = user_data[0].generate_auth_token(app, expiration)
    #         else:
    #             res = "username or password incorrect"
    #     else:
    #         res = "Incorrect behaviour"
    #     return res
    #
    # def verify_auth_token(self, token, app):
    #     """
    #     This method verify user's token
    #
    #     :param token: Token information
    #     :param app: Flask application Object
    #
    #     :return: All user data or None
    #     """
    #     user_data = None
    #     if app and token:
    #         res = tables.User.verify_auth_token(token, app)
    #         if res and res.get('id', False):
    #             user_data = self.session.query(tables.User).get(res.get('id', 0))
    #     return user_data



# todo insert new user method
"""
# Create plain user with default key complexity
john = User(name='John', password='flatten-shallow-ideal')

# Create an admin user with higher key derivation complexity
administrator = User(
    name='Simon',
    password=PasswordHash.new('working-as-designed', 15))
"""