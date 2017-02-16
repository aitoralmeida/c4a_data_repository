RestApiInterface
==================

This part is a Rest API interface to allow developers connect to City4age database and obtain
some information about users, actions, behaviours and risks.

To use some of the endpoints coded in this API, it is neccesary to have a registered account with the appropriate
role access level.


Installation requirements
--------------------------

The REST API is installed automatically as part of the installation of City4Age data repository bundle. to know how 
to install this API, refer to README documentation in the root of the projcet.


Available commands.
-------------------

The main page of the API contains the available commands with a description of each action that can perform an user.

To use some of them, it is necessary to send credential access into the system using HTTP-auth method. The credentials
could be a combination of username:password or a previously created user token. An example of how to create a token is:

```bash
    curl -u username:password -i -X GET http://0.0.0.1:5000/api/login
```

**Endpoints**

* login: Sending existing username and password this endpoint returns a session cookie amd a session token.
* logout: This delete actual session cookie and token.
* add_action: Add new action into the database.
* add_activity: Add new activity into the database.
* add_measure: Add new measure into the database.
* add_new_user: Add new user into the system (Administrator only).
* clear_user: Delete user and user data from the system (Administrator only).
* search: Search for datasets in database.


Aditional Important notes
---------------------------

This part of the project is in active developing so, it is possible that not all the functionality
can be working as indented.


DISCLAIMER
------------

Some of functions need to be re-implemented due to lack of a final database desing.