# -*- coding: utf-8 -*-

"""
This file contains different set of task to be executed by Celery Beat

"""

from celery import Celery
import subprocess as sub
import os

__author__ = "Rubén Mulero"
__copyright__ = "foo"   # we need?¿


app = Celery('tasks')
app.config_from_object('celeryconfig')

@app.task
def inference(p_d2rq_path, p_in_path, p_out_path):
    # all ok, we are going to launch Jena Rule Engine jar file
    # Execute jar file. We take this python file and put relative path to jar,
    java_call = sub.Popen(['java', '-jar', os.path.normpath(os.path.join(os.path.realpath(__file__),
                                                                         u'../../../ruleEngine/reasoner.jar'))],
                   stdout=sub.PIPE, stderr=sub.PIPE)
    output, errors = java_call.communicate()
    if not errors and output:
        # If all is OK, we copy generated archive and activate server
        print "New mapping.ttl file generated"
        print "Checking if tomcat is ready....."



        # todo make celery permissions to copy new mapping ttl
        copy = sub.Popen(['cp', os.path.normpath(os.path.join(os.path.realpath(__file__),
                                                                             u'../../../ruleEngine/mapping.ttl'))],
                              stdout=sub.PIPE, stderr=sub.PIPE)
        out, err = copy.communicate()
        if not err:
            # Copy sucesfull
            print "Mapping.ttl archive copied."

    else:
        print errors
        raise ErrorJavaException(errors)


def server_activate():
    """
    This method checks if Tomcat is running and it starts with the new infered mapping.ttl

    :return:
    """
    # Todo view a form to manage tomcat7 service. Add celery to sudoers?
    pass


# Custom Errors
class ErrorJavaException(Exception):
    def __init__(self, p_value):
        self.value = p_value

    def __str__(self):
        return "An error ocurred in java jar inference reasoner: " + str(self.value)