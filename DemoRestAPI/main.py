# -*- coding: utf-8 -*-

import sys
import os

from demo import start_demo


__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2016, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Demo"

# Prepare base dir working directory
basedir = os.path.dirname(os.path.realpath(__file__))
if not os.path.exists(os.path.join(basedir, "main.py")):
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, "main.py")):
        basedir = cwd
sys.path.insert(0, basedir)

# main execution
if __name__ == '__main__':
    # Print Welcome MSG
    print("Welcome to City4Age Rest API - Linked Data DEMO application \n"
          "============================================================= \n")

    # Starting demo
    start_demo()
    #
    print("\n"
          "END \n"
          "#############################################################")
    print("#############################################################\n")
    print("#############################################################\n")
