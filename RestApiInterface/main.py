# -*- coding: utf-8 -*-

import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from src.packFlask.api import app as application

__author__ = 'Rubén Mulero'
__copyright__ = "foo"   # we need?¿

# Prepare base dir working directory
basedir = os.path.dirname(os.path.realpath(__file__))
if not os.path.exists(os.path.join(basedir, "main.py")):
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, "main.py")):
        basedir = cwd
sys.path.insert(0, basedir)

# main execution
if __name__ == '__main__':
    # Create the log folder if not exists
    if not os.path.exists('./log'):
        os.makedirs('./log')
    # Setting logging handlers
    logHandler = RotatingFileHandler('./log/info.log', maxBytes=1024 * 1024 * 100, backupCount=20)
    # set the log handler level
    logHandler.setLevel(logging.INFO)
    # set the formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logHandler.setFormatter(formatter)
    # set the app logger level
    application.logger.setLevel(logging.INFO)
    application.logger.addHandler(logHandler)
    # Run the application
    application.run(debug=True, host='0.0.0.0')
