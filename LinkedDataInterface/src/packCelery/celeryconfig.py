# -*- coding: utf-8 -*-

"""
Celery cofniguration file. Here we can configure Cron timers and other thins like broker

"""

from celery.schedules import crontab
import os

__author__ = "Rubén Mulero"
__copyright__ = "foo"   # we need?¿

# Get actual file absolute path
file_path = os.path.realpath(__file__)
# Set json as only accepted content type serializer (improves security).
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
# Set Timezone
CELERY_TIMEZONE = 'Europe/Madrid'
# Set execution
CELERYBEAT_SCHEDULE = {
    'execute-inference': {
        'task': 'task.inference',                                       # task name
        'schedule': crontab(minute='*/1'),                              # time
        # Optional args for task.
        'args': (os.path.normpath(os.path.join(file_path, u'../../../ruleEngine/reasoner.jar')),      # Path to rule engine reasoner
                 os.path.normpath(os.path.join(file_path, u'../../../ruleEngine/mapping.ttl')),       # Path to new mapping file
                 os.path.normpath(os.path.join(file_path, u'/var/lib/tomcat7/webapps/d2rq/WEB-INF/'))) # Path to Tomcat
    },
}


# todo we need to change args paths. Only if we want to use ubuntu 16.04