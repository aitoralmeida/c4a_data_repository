Installation requirements
==========================

This install guide is for ubuntu only. Please consider install first in this GNU/Linux distribution after test in another enviroements.

RestApiInterface need the following dependencies.

1. A proper Python 2.7 interpreter.
2. Virtualenv
3. Development packages:
    1. python-dev
    2. postgresql-server-dev
    3. build-essential
4. PostgreSQL database.
5. Nginx.




###**Instalation**

To install this package you need to do this steps:

1. You need to install and configure [PostgreSQL](http://www.postgresql.org/docs/manuals/ "PostgreSQL docs")
2. Install dependencies (virtualenv, python-dev, postgresql-server-dev, Nginx)
3. Uncompress the project and place it in any path in your system:
    ```bash
        $ tar -xvf RestApiInterface.tar.gz
        $ mv RestApiInterface /destination/system/path
    ```
4. Then you need to use virtualenv to populate application:
    ```bash
        $ virtualenv /destination/system/path
    ```
5. Enter to destination path and activate virtualenv
    ```bash
        $ souurce /destination/system/path/bin/activate
    ```
6. Once you are in virtualenv your promp willbe like:
    ```bash
        (RestApiInterface)$
    ```
7. Install project dependencies.
    ```bash
        (RestApiInterface)$ pip install -r requirements.txt
    ```
8. If all is good copy **city4ageAPI** file from _scripts_ to _/etc/init_
9. Open **city4ageAPI** file and change the following:
    ```bash
        env PATH=/home/deusto/<path to destination bin folder>/bin
        chdir /home/deusto/<path to the main.py> # i.e. /home/deusto/cit4ageApi/
    ```

10. todo



11. Configure database connection. Modify **rest_api.cfg** file under _conf_ directory.


###**How to run**

1. Go to _/etc/init_ folder anr run:
    ```bash
        $ sudo start city4ageAPI
    ```
2. Execute:
    ```bash
        $ sudo service ngingx restart
    ```

3. Make sure you have PostgreSQL service running.