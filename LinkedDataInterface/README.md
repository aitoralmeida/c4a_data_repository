Installation requirements
==========================

LinkedDataInterface need some requisites:

1. A well installed and configured Tomcat server.
2. Python-Celery installed on the system.
3. A bash script or system service unit target job to launch celery
4. Java.
5. Your own "mapping.ttl" file prevoously created with D2RQ.
6. Your own "rules.txt" with several rules prepared to be infered.


###**Instalation**

To install this project you only need to place the code in any place
in your system (for example in home folder).

When you have the project placed put your *mapping.ttl* and *rules.txt* in **ruleEngine** subfolder.

Thats all.


###**How to run**

Simply:

1. Open bash console.
2. Cd to api.py
3. Execute:


```bash
celery -A task worker --loglevel=info --beat
```