# -*- coding: utf-8 -*-

"""
This file contains different set of task to be executed by Celery Beat

"""

from celery import Celery
import subprocess as sub
import os

__author__ = "Rubén Mulero"
__copyright__ = "foo"  # we need?¿

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
        check = "Checking if tomcat is ready....."
        # Subprogram to check if tomcat7 is ready
        _server_activate()
        # todo make celery permissions to copy new mapping ttl
        # Remember this is only for ubuntu. Maybe Tomca7 dir is in other path
        copy = sub.Popen(['cp', os.path.normpath(os.path.join(os.path.realpath(__file__),
                                                              u'../../../ruleEngine/mapping.ttl')),
                          u'/var/lib/tomcat7/webapps/d2rq/WEB-INF/'],
                         stdout=sub.PIPE, stderr=sub.PIPE)
        copy_out, copy_err = copy.communicate()
        if not copy_err:
            # Copy sucesfull
            print "Mapping.ttl archive copied."
        else:
            # raise ERROR
            raise MalformedException(copy_err)
    else:
        print errors
        raise ErrorJavaException(errors)


def _server_activate():
    """
    This method checks if Tomcat is running and it starts with the new infered mapping.ttl

    :return: None
    :except: ErrorTomcatLauncherException If service call fails
    """

    ####### UBUNTU ONLY -- UPSTAR
    tomcat_ready = sub.Popen(['service', 'tomcat7', 'status'], stdout=sub.PIPE, stderr=sub.PIPE)
    tomcat_ready_output, tomcat_ready_error = tomcat_ready.communicate()
    if tomcat_ready_output and not tomcat_ready_error and "with pid" not in tomcat_ready_output:
        print "Tomcat service is not activated, we are going to activate now!!!"
        # Tomcat service is not activated or something is wrong.
        tomcat_launch = sub.Popen(['service', 'tomcat7', 'start'], stdout=sub.PIPE, stderr=sub.PIPE)
        tomcat_launch_output, tomcat_launch_error = tomcat_launch.communicate()
        if tomcat_launch_error:
            # Something wrong happen, Raise Error
            raise ErrorTomcatLauncherException(tomcat_launch_error)
    elif tomcat_ready_error:
        raise MalformedException(tomcat_ready_error)
    print "Tomcat server is activated!!"


# Custom Errors
class MalformedException(Exception):
    def __init__(self, p_value):
        self.value = p_value

    def __str__(self):
        return "A general system error appeared. Error msg: " + str(self.value)


class ErrorJavaException(Exception):
    def __init__(self, p_value):
        self.value = p_value

    def __str__(self):
        return "An error ocurred in java jar inference reasoner: " + str(self.value)


class ErrorTomcatLauncherException(Exception):
    def __init__(self, p_value):
        self.value = p_value

    def __str__(self):
        return "An error ocurred when program try to launch Tomcar engine. Error msg: " + str(self.value)
