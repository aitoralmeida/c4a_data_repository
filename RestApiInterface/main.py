# -*- coding: utf-8 -*-

import sys
import os

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
    from src.packFlask.api import app
    # todo change this to --> app.run(host='0.0.0.0', port=int("231") and debug=False.
    app.run(debug=True)
