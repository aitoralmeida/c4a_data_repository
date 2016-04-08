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
# Set Timezone
CELERY_TIMEZONE = 'Europe/Madrid'
# Set execution
CELERYBEAT_SCHEDULE = {
    'execute-inference': {
        'task': 'task.inference',                                       # task name
        'schedule': crontab(minute='*/1'),                              # time
        # Args for tasj
        'args': (os.path.normpath(os.path.join(file_path, u'../../../d2rq')),             # dunmp-rdf
                 os.path.normpath(os.path.join(file_path, u'../../../d2rq/mapping.ttl')),         # in file
                 os.path.normpath(os.path.join(file_path, u'../../../d2rq/dump.rdf'))),           # out file in desired format
    },
}