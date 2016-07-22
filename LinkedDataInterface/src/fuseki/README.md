Instalation
===========

To install fuseki server engine you need to to the following tasks:

* Copy __fuseki.war__ into Tomcat's webapps folder (*/var/lib/tomcat8/webapps*)
* Create a new folder in __/etc__ called *fuseki* (__/etc/fuseki)__).
* Copy contents of *run* and *shiro.ini* file in __/etc/fuseki__ folder.
* Go to __/etc__ folder and change owned to tomcat to user and group by executing:
        ```bash
        sudo chown -R 
        ```
* Restart Tomcat8 server using systemctl command.


Configuration
=============

The configuration files are under __etc/fuseki__. Here you have this relevant files:

* *config.ttl* : Main configuration file to configure some parameters of fuseki server.
* *configuration*: A folder wich contains relevant information about datasers. Here are listed all datasets
and it is possible to confiugre some important things like if it is possbiel to read & write graphs or make
queries to actual loaded knowledge.
* *shiro.ini* : In this file is stored all configuration related to security. Here, it is possible to define
some rules to protect fuseki against malicious practices for unauthorized users.


Usage
=====

To use fuseki you have two options:

1. You can connect it via web interface using a browser. Here you can see
relevant information and change datasets info if you provide a valid user/password.
2. You can send information using a program (for example __curl__) to make some calls
like queries.