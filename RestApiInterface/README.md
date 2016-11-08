RestApiInterface
==================

This part is a Rest API interface to allow developers connect to City4age database and obtain
some information about users, actions, behaviours and risks.

To perform some actions you need to be logged in the system.



Installation requirements
--------------------------

This install guide is for Ubuntu only. Please consider install first in this GNU/Linux distribution after test in another enviroements.

RestApiInterface need the following dependencies.


* Some knowledge of GNU/Linux
* An Ubuntu Server 16.04 LTS


Available commands.
-------------------

You need to use curl and send information using JSON format style. Remember to send information with
content header JSON. Example:

```bash
    curl -X POST -k -d '{"username":"admin","password":"admin"}' https://10.48.1.49/api/0.1/login --header "Content-Type:application/json"
```

**Endpoints**

* login: Sending existing username and password this endpoint returns a session cookie.
* logout: This delete actual session cookie.
* add_action: Add new action into the database.
* add_activity: Add new activity into the database.
* add_new_user: Add new user into the system (Administrator only)
* search: Search for datasets in database.


Aditional Important notes
---------------------------

This part of the project is in active developing so, it is possible that not all the functionality
can be working as indented.


DISCLAIMER
------------

Some of functions need to be re-implemented due to lack of a final database desing.