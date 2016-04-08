# -*- coding: utf-8 -*-

"""
This file is used to connect to the database using SQL Alchemy ORM

"""

from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
import tables

__author__ = 'Rubén Mulero'
__copyright__ = "foo"   # we need?¿

# Database settings
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
        :return: False if Nothing, Something if OK
        """
        res = False
        self.session.add(p_data)         # Pending add (we can see new changes before commit)
        if self.session.new:
            res = self.session.commit()        # TODO parece que no devuelve nada
        else:
            # Raise error
            print "Can't add new data into the current session"

        return res


    def insert_all(self, p_list_data):
        """
        Insert a list of Type of datas

        :param p_list_data: List of data
        :return:
        """
        res = False
        self.session.add_all(p_list_data)         # Multiple users, pending action
        if self.session.new:
            # Todo try catch con rollback en caso de fallo
            res = self.session.commit()
        else:
            # Raise error
            print "Can't add new data into the current session"

        return res

    def query(self, p_class, **attrs):
        # TODO definir mejor

        return self.session.query(p_class)


    def close(self):
        """
        Close the connection

        :return: None
        """
        self.session.close()
