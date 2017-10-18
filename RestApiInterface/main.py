# -*- coding: utf-8 -*-


from src.packFlask.api import app as application


__author__ = 'Rubén Mulero'
__copyright__ = "Copyright 2016, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Rubén Mulero"
__email__ = "ruben.mulero@deusto.es"
__status__ = "Prototype"


# main execution
if __name__ == '__main__':
    # Run the application
    application.run(debug=True, host='0.0.0.0')     # TODO change this to false in prod
