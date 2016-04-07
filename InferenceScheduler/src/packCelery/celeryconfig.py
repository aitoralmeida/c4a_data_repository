# -*- coding: utf-8 -*-

"""
Celery cofniguration file. Here we can configure Cron timers and other thins like broker

"""

from celery.schedules import crontab

__author__ = "Rubén Mulero"
__copyright__ = "foo" # we need?¿

# Set Timezone
CELERY_TIMEZONE = 'Europe/Madrid'

# Set execution rules
CELERYBEAT_SCHEDULE = {
    'execute-inference': {
        'task': 'task.inference',                                       # task name
        'schedule': crontab(minute='*/1'),                              # time
        # Args for tasj
        'args': (u'/home/deusto/D2RQ/dump-rdf',                         # dump-rdf
                 u'/home/deusto/D2RQ/mapping.ttl',                      # in file
                 u'/home/deusto/dump.rdf'),                             # out file in desired format
    },
}