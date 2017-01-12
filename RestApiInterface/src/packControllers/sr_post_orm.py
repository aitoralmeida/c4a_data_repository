# -*- coding: utf-8 -*-

from packORM import sr_tables
from post_orm import PostORM


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

