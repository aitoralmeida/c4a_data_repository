# README #

City4Age Project's (H2020 grant agreement number 689731) LinkedData and RestAPI servers.

This repository contains two projects. 

1. LinkedDataInterface: An interface to infer new statements using a RuleEngine Reasoner and to serve it with SPARQL, Linked Data client or HTML endpoints.
2. RestApiInterface: A REST API interface to manage some user personal information in a POSTGRESQL relational database.

For more information, please read each project README.

There are other folders containing more information for installation purposes.

Requirements
-------------

To install this project you need the following requirements.

1. A local machine with Ubuntu 16.04 GNU/Linux distribution,
2. Python 2.7.
3. Python Fabric.
4. A proper server configured with Ubuntu Server 16.04 GNU/Linux distribution.


Installation
--------------

To install the entire project please follow this steps.

1. Cd to **fabfile.py**
2. Edit _env.hosts_ and _env.user_ in **fabfile.py** with your favourite editor:
    1. _env.host_ : Array of server hosts. Put here your destination(s) server(s)
    2. _env.user_ : User to login in.
3. Save and exist
4. Run:
    ```bash
        fab fabfile.py
    ```
    to see all available commands.
5. Run:
    ```bash
        fab main_install
    ```
    To install entire project


Additional important notes
-----------------------------

All needed dependencies for the project are installed automatically. The user does not need to bother about this issue. However, here is a complete list of project dependencies and some advices:

* Python 2.7
* Python-dev (2.7)
* PostgreSQL 9.5
* PostgreSQL Server Dev
* Virtualenv  for Python 2.7
* Build-essential (gc++ compiler, fakeroot.....)
* Nginx
* Python-Celery (Executes python code in a period of time)
* Rabbitmq Server
* OpenJDK-8 (JRE and JDK
* Tomcat 8
* Apache Ant

You must provide a ssh password to establish connection to the server and run some
_sudo_ commands.

In some steps, application may ask some things such as ssl keys generation, d2rq mapping.tll
file verification or rules verification.

License
----------

This project is licensed under the terms of the GPL v3 license.

