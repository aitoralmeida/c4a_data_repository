Installation requirements
==========================

LinkedDataInterface need some requisites:

* A well installed and configured Tomcat server.
* Python-Celery installed on the system.
* Java 1.8 (OpenJDK).
* Your own "mapping.ttl" file prevoously created with D2RQ.
* Your own "rules.txt" with several rules prepared to be infered.
* Some knowledge of GNU/Linux.


###**Instalation**

To install this project you need to perform the following actions:

1. Uncompress and place the code in any place in your system (for example in home folder).
2. When you have the project placed put your *mapping.ttl* and *rules.txt* in **ruleEngine** subfolder.
3. Create a new user called celery.
4. Change folder owner to new user called celery(make sure you put right permissions levels).
5. Copy *celerybeat.conf* and *celeryd.conf* from **scripts** subfolder into:
    ```bash
    /etc/init
    ```
6. Run command:
    ```bash
    initctl reload-configuration
    ```
    Performing this Ubuntu will discover new system unit services.

Thats all.


###**How to run**

Simply:

1. Open a Linux terminal.
2. Launch celery in this order:
    ```bash
    service celeryd start
    service celerybeat start
    ```