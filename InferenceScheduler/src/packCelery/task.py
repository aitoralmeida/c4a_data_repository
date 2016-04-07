# -*- coding: utf-8 -*-

"""
This file contains different set of task to be executed by Celery Beat

"""

from celery import Celery
import subprocess as sub


app = Celery('tasks')
app.config_from_object('celeryconfig')

@app.task
def inference(p_d2rq_command, p_in_path, p_out_path):
    # launch D2RQ dump-rdf command
    p = sub.Popen(("/bin/bash", p_d2rq_command, "-f", u'RDF/XML', "-o", p_out_path, p_in_path),
                   stdout=sub.PIPE, stderr=sub.PIPE)
    out, errors = p.communicate()
    if len(errors) == 0:
        # all ok, we are going to launch Jena Rule Engine jar file
        # Execute jar file to infer with our rules
        sub.call(['java', '-jar', '/home/deusto/PycharmProjects/c4a_data_infrastructure/InferenceScheduler/lib/reasoner.jar'])
        # todo afert all is done test if ok an restar D2R server


        #### Restar D2R server

    else:
        raise ErrorRDFException(errors)

class ErrorRDFException(Exception):
    def __init__(self, p_value):
        self.value = p_value

    def __str__(self):
        return "An error ocurred in inference task: " + str(self.value)