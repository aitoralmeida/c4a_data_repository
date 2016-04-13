# -*- coding: utf-8 -*-

"""
This file is used to connect to the database using SQL Alchemy ORM

"""

import tables
import ConfigParser
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

__author__ = 'Rubén Mulero'
__copyright__ = "foo"   # we need?¿


# Database settings
config = ConfigParser.ConfigParser()
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

    def query(self, p_class, **attrs):
        # TODO define better

        return self.session.query(p_class)


    def commit(self):
        """
        Commit all data and close the connection to DB.

        :return: None
        """
        if self.session.new:  # todo check if we need to know that session is new or not
            try:
                self.session.commit()
            except:
                self.session.rollback()
            finally:
                self.session.close()
        else:
            print "Session is not new. Check it"

    def close(self):
        """
        Force close the connecion of the actual session

        :return: None
        """
        if self.session:
            self.session.close()    # todo Session return anything?
