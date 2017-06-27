# -*- coding: utf-8 -*-

from datetime import datetime

__author__ = 'Gorka Azkune'
__copyright__ = "Copyright 2017, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Gorka Azkune"
__email__ = "gorka.azkune@deusto.es"
__status__ = "Prototype"

class ExpertActivityModel:
    
    def __init__(self, name=None, infodict=None):
        """ Constructor
        
        Usage example:
            eam = ExpertActivityModel("MakeChocolate", eamdict)
            
        Parameters
        ----------
        name : string
            the name of the target activity
        infodict : dict
            a dict with the information related to an EAM (usually read from a JSON file)
                    
        Returns
        ----------
        Instance of the class
        
        """
        
        if name is not None and isinstance(infodict, dict):
            self.name = name
            self.locations = infodict["locations"]
            self.actions = infodict["actions"]
            self.duration = infodict["duration"]
            # convert strings to datetime types
            #self.start = infodict["start"]
            self.start = []
            self.convert_start_list(infodict["start"])
        else:
            self.name = ""
            self.locations = []
            self.actions = []
            self.duration = -1
            self.start = []
        

    def print_eam(self):
        """ Method to print an instance of EAM
        
        Usage example:
            print_eam()
            
        Parameters
        ----------
        None
                    
        Returns
        ----------
        None
        
        """
        print self.name
        print '   locations:', self.locations
        print '   actions:', self.actions
        print '   duration:', self.duration
        print '   start:'
        for timerange in self.start:
            print '    ', timerange[0].strftime("%H:%M"), '-', timerange[1].strftime("%H:%M")
        
    def convert_start_list(self, rangelist):
        """ Method to convert time ranges read from the dict to datetime type
        
        Usage example:
            convert_start_list(rangelist)
            
        Parameters
        ----------
        rangelist : list
            a list of strings, with the start time ranges
                            
        Returns
        ----------
        None
        
        """
        for timerange in rangelist:
            time1 = datetime.strptime(timerange[0], "%H:%M")
            time2 = datetime.strptime(timerange[1], "%H:%M")
            self.start.append([time1, time2])