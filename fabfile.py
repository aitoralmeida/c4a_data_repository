from fabric.api import run, env, sudo
from fabric.context_managers import cd


####################################
####################################
######### Set servers information

env.hosts = [
    '10.48.1.19',
    # Second.server.com,
    # third.server.es,
    # and.so.on ......
]

# Set the username
env.user = "city4age"

# Set pwd
env.password = "city4age"   # TODO we must remove it


####################################
####################################
######### Installation functions.

# For the momment we assume that the project is in /home dir maybe we will change this to /opt
# this require to create folders with user=city4age and change permissions

# todo examples
# Create a directory as another user
# sudo("mkdir /var/www/web-app-one", user="web-admin")


def _install_deps():
    """
    Install needed dependencies

    :return:
    """
    sudo('apt-get install python-dev postgresql-9.5 postgresql-server-dev-9.5 virtualenv build-essential nginx '
         'python-celery rabbitmq-server openjdk-8-jre')


def _deploy():
    """
    Deploy all city4age project in a destination directory and change the user to the actual one.

    :return:
    """
    with cd('/opt'):
        sudo('git clone https://elektro108@bitbucket.org/elektro108/c4a_data_infrastructure.git')
        sudo ('chown' + env.user + ':' + env.user)

    """
    with cd('/opt/c4a_data_infrastructure'):
        run('virtualenv ./LinkedDataInterface')
        run('virtualenv ./RestApiInterface')
    """


def _create_databbase():
    """
    Create basic structure of databsae

    :return:
    """

    # TODO we need to dump an image to postgresql

    # The idea is to create a new user in database called city4agedb and restore all database tables

    """
    with cd('/opt/c4a_data_infrastructure/RestApiInterface'):
        run('./bin/python ./src/packORM/create_tables.py')
    """
    pass


def _install_rest_api():
    """
    Install Rest API Interface in the server.

    :return:
    """
    with cd('/opt/c4a_data_infrastructure/RestApiInterface/scripts'):
        run('/bin/bash ./install.sh')


def _install_linked_data():
    """
    Install Linked Data Interface in the server.

    :return:
    """
    with cd('/opt/c4a_data_infrastructure/LinkedDataInterface/scripts'):
        run('/bin/bash ./install.sh')


def main_install():
    """
    Install entire project in the server:
            --> Rest API Interface
            --> Linked Data Interface
    :return:
    """
    # We ask to user the name of the current user of the machine and we make the connection
    _deploy()
