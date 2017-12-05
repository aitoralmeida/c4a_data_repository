# -*- coding: utf-8 -*-

import sys, getopt
import time, datetime
import logging

import numpy as np
import pandas as pd
import json
import itertools

from expert_activity_model import ExpertActivityModel
from Pattern import Pattern
from Cluster import Cluster
from LogReader import LogReader
from ad_pattern_filter import ADPatternFilter


__author__ = 'Gorka Azkune'
__copyright__ = "Copyright 2017, City4Age project"
__credits__ = ["Rubén Mulero", "Aitor Almeida", "Gorka Azkune", "David Buján"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Gorka Azkune"
__email__ = "gorka.azkune@deusto.es"
__status__ = "Prototype"


class PatternModelMatching:    
    
    def __init__(self, eamlist, annotatedfile, logfile):
        """
        Constructor of the class


        :param eamlist: A lis of eams
        :param basestring annotatedfile: The name of the CSV file (CASAS format) where the patterns found by AD are
        :param basestring logfile:  The name of a text file generated as a log of the AD tool
        :param string or None contextfile: The name of the JSON file where the context model in defined

        :returns Instance of the class

        """

        # TODO comment that annontated file is a CSV pandas instance containing the needed data

        self.eamlist = eamlist


        self.annotatedfile = annotatedfile


        self.logfile = logfile


        # We may not need to read the logfile and extract the pattern and cluster lists
        self.patternlist = []
        self.clusterlist = []
        # Attribute to store a dict of eam indices and all their possible combinations
        self.eamcombinations = {}        

        # For the maximization problem, build already all the combinations of EAM
        # indices
        eamindex = range(0, len(self.eamlist))
        for i in eamindex:
            # eams = list(itertools.combinations(eamindex, i))
            self.eamcombinations[i] = list(itertools.combinations(eamindex, i + 1))
            # print i
            # print self.eamcombinations[i]
            # print '-----------------------------------'

    # TODO consider to delete it
    def load_annotated_data(self):
        """ Method to load the annotated data csv file generated by CASAS AD into a pandas dataframe
            
        Usage example:
            load_annotated_data()
                
        Parameters
        ----------
        None
                
        Returns
        -------
        None
        
        """
        #self.df = pd.read_csv(self.annotatedfile, parse_dates=[[0, 1]], header=None, index_col=0, sep='\t')
        #self.df.columns = ['location', 'action', 'event', 'pattern', 'executed_action']
        #self.df.index.names = ["timestamp"]

        self.df = pd.read_csv(self.annotatedfile, parse_dates=[[0, 1]], header=None, sep='\t')
        self.df.columns = ['timestamp', 'location', 'action', 'event', 'pattern', 'executed_action']



    def annotate_data_frame(self, start, end, bestnames):
        """ Method to store the detected EAMs in the internal dataframe as a new column (detected_activities)
            
        Usage example:
            start = pd.Timestamp('2016-01-01 00:00:00')
            end = pd.Timestamp('2016-01-01 00:00:12')
            bestnames = ['MakeCoffee', 'MakePasta']
            annotate_data_frame(start, end, bestnames)
                
        Parameters
        ----------
        start : Pandas.Timestamp
            start time of the action sequence to annotate
        end : Pandas.Timestamp
            end time of the action sequence to annotate
        bestanames : list
            a list of strings with the names of the best EAMs found
                
        Returns
        -------
        None
        
        """
        aux_df = self.df[start:end+1]
        for index in aux_df.index:
            self.df.set_value(index, 'detected_activities', bestnames)


    def prefilter_patterns(self):
        """ Method to filter spurious patterns before the matching phase. Filtered
        patterns are annotated as 'Other_Activity' in self.df (pandas dataframe)
            
        Usage example:
            prefilter_patterns()
                
        Parameters
        ----------
        None
                
        Returns
        -------
        None
        
        """
        prefilter = ADPatternFilter(self.logfile)
        prefilter.filter_patterns()
        auxlist = ['Pat_%s' % (x.number) for x in prefilter.removedPatterns]
        
        for index in self.df.index:
            pattern = self.df.loc[index, 'pattern']            
            if pattern in auxlist:
                self.df.loc[index, 'pattern'] = 'Other_Activity'

    def process_patterns(self):
        """ Method to iterate through the dataframe (self.df), extract patterns and calculate the suitability of EAMs for that
        pattern.
            
        Usage example:
            process_patterns()
                
        Parameters
        ----------
        None
                
        Returns
        -------
        None
        
        """
        # TESTING!! Use the prefilter based
        self.prefilter_patterns()
        # Filter all the actions tagged as Other_Activity
        auxdf = self.df[self.df["pattern"] != "Other_Activity"]
        actions = []
        locations = []
        pat = ""
        start = None
        end = None
        previous = None
        start_index = None
        end_index = None
        previous_index = None
        # Add a new column to self.df for the activities detected by the algorithm
        # The new column is initialized with 'None'
        detected_activities = [['None']]*len(self.df)
        self.df['detected_activities'] = detected_activities
        for index in auxdf.index:                               # Lines in which casas encountered something
            if auxdf.loc[index, "pattern"] != pat:
                if len(actions) > 0:
                    print 'New pattern'
                    print '   actions:', actions
                    end = previous
                    end_index = previous_index
                    # Call here to the real matcher                    
                    [maxscore, bestnames, partialscores] = self.find_models_for_pattern(locations, actions, start, end)
                    # TESTING!! Action based filter  
                    if partialscores[0] == -1:
                        bestnames = ['None']
                        
                    # TESTING!! Number of activities greater than number of actions                        
                    if len(bestnames) > len(actions):
                        bestnames = ['None']                        
                    
                        
                    print '   start:', start, 'end:', end
                    print '   best eams:', bestnames, '(', maxscore, ')'
                    print '   partial scores: a(', partialscores[0], '), d(', partialscores[1], '), s(', partialscores[2], '), l(', partialscores[3], ')'
                    self.annotate_data_frame(start_index, end_index, bestnames)
                
                # Assign start the index value (the timestampt itself)
                start = auxdf.loc[index, 'timestamp']
                start_index = index
                #print 'New pattern!', auxdf.loc[timestamp, "pattern"]                
                pat = auxdf.loc[index, "pattern"]
                actions = []
                locations = []
                
            actions.append(auxdf.loc[index, "action"])
            locations.append(auxdf.loc[index, "location"])
            previous = auxdf.loc[index, 'timestamp']
            previous_index = index
            
    def shared_actions(self, actions, eamindices):
#        print 'EAMS:', eams
#        print 'Actions:', actions
        actions = set(actions)        
        for i in eamindices:
            eamactions = self.eamlist[i].actions
            eamactions = set(eamactions)
            if len(actions.intersection(eamactions)) == 0:
                return False
                
        return True
        
    def find_models_for_pattern(self, locations, actions, start, end):
        """ Method to calculate for a given pattern (sensors, actions, start, end), the best list of EAMs
        to explain the pattern
            
        Usage example:
            start = pd.Timestamp('2016-01-01 00:00:00')
            end = pd.Timestamp('2016-01-01 00:00:12')
            find_models_for_pattern(sensors, actions, start, end)
                
        Parameters
        ----------
        actions: list
            a list of actions
        locations: list
            a list of locations for actions
        start : Pandas.Timestamp
            start time of the action sequence that compose the detected patter
        end : Pandas.Timestamp
            end time of the action sequence that compose the detected patter
                
        Returns
        -------
        maxscore: float
            a float number in [-1, 1] with the maximum score of all combinations of EAMs
        bestnames: list
            a list of strings which represent the target activities
        partialscores: list
            a list of floats in [-1, 1] for the scores obtained for each function of the cost function
        
        """
        # define the weights of the cost function
        # Weights for the test with synthetic data
#        wa = 1        
#        wl = 1
#        wd = 0.2 
#        ws = 0.7
        # Weights for the test with Kasteren dataset
        # F1 score (macro) = 0.77
        wa = 1.3 #1.3
        wl = 1.0 #1.0
        wd = 0.1 #0.1
        ws = 1.5 #1.5
        #wt = 1
        # We will use a strong force search, testing all the posible combinations
        # of eams and returning the combination with the highest score
        maxscore = -sys.maxint
        partialscores = []
        bestnames = []
        for key in self.eamcombinations:
            # This is the list of EAM indices for combination level 'key' 
            eams = self.eamcombinations[key]            
            for i in xrange(len(eams)):
                # Testing!!
                # Onyl consider those combinations of EAMs where shared actions for
                # all EAMs exist
                if self.shared_actions(actions, eams[i]) == False:                                        
                    continue
                
                # Extract the EAM names of the current combination of EAMs
                names = [self.eamlist[j].name for j in eams[i]]
                #print '   ', names
                score_actions = self.func_actions(actions, eams[i])
                #score_time = self.func_time(start, end, eams[i])
                score_duration = self.func_duration(start, end, eams[i])
                score_start_time = self.func_start_time(start, eams[i])
                score_locations = self.func_locations(locations, eams[i])

                score = wa*score_actions + wd*score_duration + ws*score_start_time + wl*score_locations                
                
                #print '   score:', score, 'SA:', score_actions, 'ST:', score_time
#                if score > maxscore and len(actions) >= len(bestnames):
                if score > maxscore:
                    maxscore = score
                    bestnames = names
                    # store also the partial scores of each metric
                    partialscores = []
                    partialscores.append(score_actions)
                    partialscores.append(score_duration)
                    partialscores.append(score_start_time)
                    partialscores.append(score_locations)
                    
        # This if is done for those cases where no EAM shares actions with the pattern
        if len(partialscores) == 0:
            maxscore = -sys.maxint
            partialscores = [-1, -1, -1, -1]
            bestnames = ['None']
        return maxscore, bestnames, partialscores
            
    
    def func_actions(self, actions, eamindices):
        """ Method to calculate the suitability of the actions of a pattern compared to
        the actions of the given EAMs
            
        Usage example:
            score = func_actions(actions, eamindices)
                
        Parameters
        ----------
        actions : list
            a list of actions extracted from the pattern
        eamindices : list
            a list of intergers for the indices of EAMs in self.eamlist        
                
        Returns
        -------
        score : float
            a float number in [-1, 1] with the score of the function for the given EAMs        
        
        """        
             
        eamactions = []        
        for i in eamindices:
            eamactions.extend(self.eamlist[i].actions)            
            
        eamactions = set(eamactions)
        actions = set(actions)
        
        intersect = eamactions.intersection(actions)
        lactions = float(len(actions))
        lintersect = float(len(intersect))
        leams = float(len(eamactions))
        #score = float((len(intersect) / len(actions)) - ((len(eamactions) - len(intersect))/len(eamactions)))
        score = float((lintersect / lactions) - ((leams - lintersect)/leams))
        
        #print '   A: actions:', actions, 'eamactions:', eamactions, 
        #print '   ', len(actions), len(eamactions), len(intersect), score
        
        return score
    

    def func_start_time(self, start, eamindices):
        """ Method to calculate the suitability of start of the pattern given the EAMs
            
        Usage example:
            start = pd.Timestamp('2016-01-01 00:00:00')
            score = func_start_time(start, eamindices)
                
        Parameters
        ----------
        start : Pandas.Timestamp
            start time of the action sequence that compose the detected patter
        eamindices : list
            a list of intergers for the indices of EAMs in self.eamlist        
                
        Returns
        -------
        score : float
            a float number in [-1, 1] with the score of the function for the given EAMs
        
        """        
        start_p = datetime.datetime.strptime(start.strftime("%H:%M:%S"), "%H:%M:%S")
        # This list will store the highest score obtained by each of the EAMs
        eamscores = []
        for i in eamindices:
            ranges = self.eamlist[i].start
            # As an EAM may have several time ranges, partial scores will be calculated
            # and afterwards, the masimum score will be stored in eamscores
            partialscores = []
            for timerange in ranges:
                start_eam = timerange[0]
                end_eam = timerange[1]
                if start_p >= start_eam and start_p <= end_eam:
                    # The start time of the pattern is inside the range of the EAM
                    partialscores.append(1)
                elif start_p < start_eam:
                    # Apply a linear decreasing function where -1 is the minimum value
                    diff = start_eam - start_p
                    diff = diff.total_seconds()
                    k = 1.0
                    b = 0.1
                    partialscores.append(max(-1, k/diff - b))
                else:
                    # start_p > end_eam
                    # Apply a linear decreasing function where -1 is the minimum value
                    diff = start_p - end_eam
                    diff = diff.total_seconds()
                    k = 1.0
                    b = 0.1
                    partialscores.append(max(-1, k/diff - b))
            
            # We already have the partial scores for an EAM; keep only the maximum
            eamscores.append(max(partialscores))
            
        # At this point we have the best score for all EAMs in eamindices
        return sum(eamscores) / len(eamscores)
    
    
    def func_duration(self, start, end, eamindices):
        """ Method to calculate the duration suitability of the pattern and the given EAMs
            
        Usage example:
            start = pd.Timestamp('2016-01-01 00:00:00')
            end = pd.Timestamp('2016-01-01 00:00:12')
            score = func_duration(start, end, eamindices)
                
        Parameters
        ----------
        start : Pandas.Timestamp
            start time of the action sequence that compose the detected patter
        end : Pandas.Timestamp
            start time of the action sequence that compose the detected patter
        eamindices : list
            a list of intergers for the indices of EAMs in self.eamlist        
                
        Returns
        -------
        score : float
            a float number in [-1, 1] with the score of the function for the given EAMs
        
        """
        
        pat_duration = (end - start).total_seconds()
        eam_duration = 0
        for i in eamindices:
            eam_duration = eam_duration + self.eamlist[i].duration
            
        delta = abs(eam_duration - pat_duration)
        # delta stores the duration difference between the pattern and the EAMs
        k = 0.001
        score = max(-1, 1 - k*delta)
        return score
        
    # The time suitability function; start and end are timestamps for the pattern
    def func_time(self, start, end, eamindices):
        """ Method to calculate the time suitability of the pattern and the given EAMs.
        This function is not currently used. Its idea was to take into account the duration
        and starting time in the same function.
            
        Usage example:
            start = pd.Timestamp('2016-01-01 00:00:00')
            end = pd.Timestamp('2016-01-01 00:00:12')
            score = func_time(start, end, eamindices)
                
        Parameters
        ----------
        start : Pandas.Timestamp
            start time of the action sequence that compose the detected patter
        end : Pandas.Timestamp
            start time of the action sequence that compose the detected patter
        eamindices : list
            a list of intergers for the indices of EAMs in self.eamlist        
                
        Returns
        -------
        score : float
            a float number in [-1, 1] with the score of the function for the given EAMs
        
        """
        # This list will store the highest score obtained by each of the EAMs
        eamscores = []
        # start and end are pandas timestamps with day, month and year info 
        # in order to calculate the difference, we need to get rid of year, month, day info
        start_p = datetime.datetime.strptime(start.strftime("%H:%M:%S"), "%H:%M:%S")
        end_p = datetime.datetime.strptime(end.strftime("%H:%M:%S"), "%H:%M:%S")
        #print '   start_p:', start_p, 'end_p:', end_p
        for i in eamindices:
            ranges = self.eamlist[i].start
            # As an EAM may have several time ranges, partial scores will be calculated
            # and afterwards, the masimum score will be stored in eamscores
            partialscores = []
            for timerange in ranges:
                start_eam = timerange[0]
                end_eam = timerange[1]
                #print '   start_eam:', start_eam, 'end_eam:', end_eam
                # Apply the equation for time suitability
                if start_eam < end_p:
                    # EAM is in the left hand side of the pattern
                    # Check whether there is any overlap
                    if end_eam < start_p:
                        partialscores.append(-1)
                    else:
                        # We have an overlap
                        # Take into account that we are operating with timestamps
                        # and datetime.timedelta
                        timedelta1 = end_p - start_eam
                        delta1 = timedelta1.total_seconds()
                        timedelta2 = end_eam - start_p
                        delta2 = timedelta2.total_seconds()
                        overlap = float(delta1) / float(delta2)
                        partialscores.append(min(1, 2*overlap - 1)) # overlap - (1 - overlap)
                else:
                    # The EAM is outside the pattern range (right)
                    partialscores.append(-1)
            
            # We already have the partial scores for an EAM; keep only the maximum
            eamscores.append(max(partialscores))
            
        # At this point we have the best score for all EAMs in eamindices
        return sum(eamscores) / len(eamscores)
         
    
    def func_locations(self, locations, eamindices):
        """ Method to calculate the location suitability of the pattern and the given EAMs.
                    
        Usage example:            
            score = func_locations(sensors, eamindices)
                
        Parameters
        ----------
        locations : list
            a list of locations that compose the detected pattern.
        eamindices : list
            a list of intergers for the indices of EAMs in self.eamlist        
                
        Returns
        -------
        score : float
            a float number in [-1, 1] with the score of the function for the given EAMs
        
        """
        #locations = []


        #for sensor in sensors:
        #    obj = self.contextmodel["sensors"][sensor]["attached-to"]
        #    location = self.contextmodel["objects"][obj]["location"]
        #    locations.append(location)
            
        locations = set(locations)
                
        eamlocations = []
        for i in eamindices:
            eamlocations.extend(self.eamlist[i].locations)
            
        eamlocations = set(eamlocations)
        intersect = eamlocations.intersection(locations)
        llocations = float(len(locations))
        lintersect = float(len(intersect))
        leams = float(len(eamlocations))
        #score = float((len(intersect) / len(actions)) - ((len(eamactions) - len(intersect))/len(eamactions)))
        score = float((lintersect / llocations) - ((leams - lintersect)/leams))
        
        return score
        
    
    def store_result(self, filename):
        """ Method to store the internal dataframe in a csv file.

        Usage example:
            store_result("results.csv")

        Parameters
        ----------
        filename : string
            a string that represents the CSV file to store the results

        Returns
        -------
        None
        
        """
        self.df.to_csv(filename, index=False)

    def store_result_database(self, p_database, p_user_in_role):
        """
        This is an alternative method that allows to store data in a DATABASE given its needed connections

        It is important to know that this is not a parametrized method


        :return: True if all is OK
                False if not
        """

        res = False
        if 'detected_activities' in self.df.columns:
            # Data and index row of the given dataFrame
            start_date = None
            end_date = None
            start_date_index = None
            end_date_index = None
            # Action and previous action
            action = None
            previous_action = None
            # We have executed well this method because we have results
            for index, row in self.df.iterrows():
                    # Check if the action is none or equals to the last one
                    action = row['detected_activities']
                    if action[0] == 'None' and start_date is not None and end_date is not None:
                        # We have valid data to insert in DB
                        aux_df = self.df[start_date_index:end_date_index+1]
                        p_database.add_discovered_activities(aux_df, p_user_in_role)
                        # Deleting the data
                        start_date = None
                        end_date = None
                        start_date_index = None
                        end_date_index = None
                        previous_action = None
                    elif action != previous_action and start_date is not None and end_date is not None:
                        # We have valid data to insert in DB
                        aux_df = self.df[start_date_index:end_date_index+1]
                        p_database.add_discovered_activities(aux_df, p_user_in_role)
                        # Update data with the current valid one
                        start_date = self.df.loc[index, 'timestamp']
                        end_date = self.df.loc[index, 'timestamp']
                        start_date_index = index
                        end_date_index = index
                        previous_action = action
                    elif action[0] != 'None':
                        # Add more data to the current one
                        if start_date is None:
                            # First action date
                            start_date = self.df.loc[index, 'timestamp']
                            start_date_index = index
                        end_date = self.df.loc[index, 'timestamp']
                        end_date_index = index
                        previous_action = action
            # When the iteration has finished, we recheck if we have some data
            if previous_action is not None and start_date is not None and end_date is not None:
                # Insert the last action in DB
                aux_df = self.df[start_date_index:end_date_index+1]
                p_database.add_discovered_activities(aux_df, p_user_in_role)
            # For the moment, we 'assume' that everything is ok
            res = True

        return res

    def filter_with_actions(self, action_score):
        """ Method to filter based on action metrics.
                    
        Usage example:            
            score = filter_with_actions(actions_score)
                
        Parameters
        ----------
        action_score : float
            a float in [1, 1] for the action suitability score
                        
        Returns
        -------
        filter : boolean
            True, if the pattern has to be filtered, False otherwise
        
        """
        if action_score == -1:
            return True
        else:
            return False    
            
            
            
########################################################################################################################          
 

def parse_args(argv):    
    """ Function to parse arguments from command line
                    
    Usage example:            
        [eamsfile, annotatedfile, logfile, contextmodel, outputfile] = parse_args(argv[1:])
                
    Parameters
    ----------
    argv : list
        the arguments to be parsed as passed to the function
                        
    Returns
    -------
    eamsfile : string
        the file name for the EAMs
    annotatedfile : string
        the file name for the output file of AD (CASAS tool)
    logfile : string
        the file name for the log generated by AD (CASAS tool)
    contextfile : string
        the file for the context model (JSON)
    outputfile : string
        the CSV file name where results have to be stored
        
    """
    eamsfile = ''
    annotatedfile = ''
    logfile = ''
    contextfile = ''
    outputfile = ''   
   
    try:
        opts, args = getopt.getopt(argv,"he:a:l:c:o:",["efile=", "afile=", "lfile=", "cfile=", "ofile="])
    except getopt.GetoptError:
        print 'PatternModelMatching.py -e <eamsfile> -a <annotatedfile> -l <logfile> -c <contextfile> -o <outputfile>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'PatternModelMatching.py -e <eamsfile> -a <annotatedfile> -l <logfile> -c <contextfile> -o <outputfile>'
            sys.exit()
        elif opt in ("-e", "--efile"):
            eamsfile = arg
        elif opt in ("-a", "--afile"):
            annotatedfile = arg
        elif opt in ("-l", "--lfile"):
            logfile = arg
        elif opt in ("-c", "--cfile"):
            contextfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
         
    return eamsfile, annotatedfile, logfile, contextfile, outputfile
  
"""
Main function
"""
def main(argv):    
    """ Main
            
    Usage example:
        main(argv)
            
    Parameters
    ----------
    argv : list
        the arguments to be parsed as passed to the function
                
    Returns
    -------
    None
        
    """
    # call the argument parser 
    [eamsfile, annotatedfile, logfile, contextmodel, outputfile] = parse_args(argv[1:])
    print 'Provided arguments:'       
    print eamsfile, annotatedfile, logfile, contextmodel
   
    matcher = PatternModelMatching(eamsfile, annotatedfile, logfile, contextmodel)
    matcher.load_EAMs()
   
    for eam in matcher.eamlist:
        eam.print_eam()
        print '-----------------------'
     
    matcher.load_annotated_data()
    #print matcher.df.head(50)
    matcher.process_patterns()
    matcher.store_result(outputfile)
