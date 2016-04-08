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
    # launch D2RQ dump-rdf command
    p = sub.Popen(("/bin/bash", p_d2rq_path + u'/dump-rdf', "-f", u'RDF/XML', "-o", p_out_path, p_in_path),
                   stdout=sub.PIPE, stderr=sub.PIPE)
    out, errors = p.communicate()
    if len(errors) == 0:
        # all ok, we are going to launch Jena Rule Engine jar file
        # Execute jar file. We take this python file and put relative path to jar,
        java_call = sub.Popen(['java', '-jar', os.path.normpath(os.path.join(os.path.realpath(__file__),
                                                                             u'../../../ruleEngine/reasoner.jar'))],
                       stdout=sub.PIPE, stderr=sub.PIPE)
        output, err = java_call.communicate()
        if not err and output:
            # Start D2RQ server if neededcd

            # todo review server execution
            q = sub.Popen(("/bin/bash", p_d2rq_path + u'/d2r-server', 'mapping.ttl'),
                          stdout=sub.PIPE, stderr=sub.PIPE)
            outp, errs = q.communicate()
            print outp
            print errs



        else:
            raise ErrorJavaException(err)
    else:
        raise ErrorRDFException(errors)


# Custom Errors
class ErrorRDFException(Exception):
    def __init__(self, p_value):
        self.value = p_value

    def __str__(self):
        return "An error ocurred in inference task: " + str(self.value)

class ErrorJavaException(Exception):
    def __init__(self, p_value):
        self.value = p_value

    def __str__(self):
        return "An error ocurred in java jar inference reasoner: " + str(self.value)