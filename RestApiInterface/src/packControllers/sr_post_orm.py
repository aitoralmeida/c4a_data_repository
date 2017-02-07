# -*- coding: utf-8 -*-

from packORM import sr_tables
from post_orm import PostORM
from sqlalchemy import MetaData


__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2016, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"


class SRPostORM(PostORM):

    def __init__(self):
        PostORM.__init__(self)

    def create_tables(self):
        """
        Create database tables
        :return:
        """
        return sr_tables.create_tables(self.engine)

    def get_tables(self):
        """
        List current database tables in DATABASE active connection (Current installed system).

        :return: A list containing current tables.
        """
        m = MetaData()
        m.reflect(self.engine, schema='city4age_sr')
        return m.tables.keys()
