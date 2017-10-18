# -*- coding: utf-8 -*-

import packFlask
import packORM
import packUtils

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from src.packORM import database_generator
from src.packControllers import ar_post_orm, sr_post_orm
from src.packFlask.api import app as application


# Prepare base dir working directory
basedir = os.path.dirname(os.path.realpath(__file__))
if not os.path.exists(os.path.join(basedir, "main.py")):
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, "main.py")):
        basedir = cwd
sys.path.insert(0, basedir)


# Create the log folder if not exists
if not os.path.exists(os.path.join(basedir, "./log")):
    os.makedirs(os.path.join(basedir, "./log"))
# Check if database is created and inserts data if it is necessary
logging.debug("Checking if database is created and creating it if it is necessary")
database_generator.generate_database(ar_post_orm.ARPostORM(), sr_post_orm.SRPostORM())
# Setting logging handlers
logHandler = RotatingFileHandler(os.path.join(basedir, "./log/info.log"), maxBytes=1024 * 1024 * 100,
                                 backupCount=20)
# set the log handler level
logHandler.setLevel(logging.INFO)
# set the formatter
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
logHandler.setFormatter(formatter)
# set the app logger level
application.logger.setLevel(logging.INFO)
application.logger.addHandler(logHandler)
