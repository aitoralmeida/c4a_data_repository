from fabric.api import run, env, sudo, prefix
from fabric.context_managers import cd
import random


##### Server configuration

# Server Hosts
env.hosts = [
    '10.48.1.115:5800',
    # 'odin.deusto.es:5800',
    # third.server.es,
    # and.so.on ......
]

# Set the username
env.user = "city4age"

# Set database creation parameters (Remember to change your mapping.ttl file)
DB_USER = 'city4agedb'      # User login
DB_PASS = 'city4agedb'      # User password (stored encrypted in db)
DB_DATABASE = 'city4agedb'     # Database name


###### Install methods

def _install_deps():
    """
    Install needed dependencies

    :return:
    """
    sudo('apt-get update && apt-get -y install python-dev postgresql-9.5 postgresql-server-dev-9.5 virtualenv '
         'build-essential nginx python-celery rabbitmq-server openjdk-8-jre tomcat8 '
         'python-celery-common ant openjdk-8-jdk')


def _deploy():
    """
    Deploy all city4age project in a destination directory and change the user to the actual one.

    :return:
    """
    with cd('/opt'):
        sudo('git clone https://github.com/aitoralmeida/c4a_data_repository.git')
        sudo('chown -R ' + env.user + ':' + env.user + ' c4a_data_repository')
        with cd('/opt/c4a_data_repository'):
            run('virtualenv ./LinkedDataInterface')
            run('virtualenv ./RestApiInterface')
            with cd('/opt/c4a_data_repository'):
                with prefix('source ./LinkedDataInterface/bin/activate'):
                    run('pip install -r ./LinkedDataInterface/requirements.txt')
                    run('deactivate')
                with prefix('source ./RestApiInterface/bin/activate'):
                    run('pip install -r ./RestApiInterface/requirements.txt')
                    run('deactivate')


def _create_database():
    """
    Send user, password and table to create a new database and then, restore all data.

    :return:
    """
    # WORKAROUND: We need to change default PostgreSQL config file to change "peer" connection to "md5"
    # to avoid some problems with psql.
    random_numer = random.randint(100, 999)
    temp_file = '/tmp/out.tmp.%s' % random_numer
    with cd('/etc/postgresql/9.5/main'):
        sudo("sed -e '90s/peer/md5/g' ./pg_hba.conf > " + temp_file + " && mv " + temp_file + " ./pg_hba.conf")
        # Restart postgres
        sudo('systemctl restart postgresql.service')

    # Create user, database and restore data.
    sudo('psql -c "CREATE USER %s WITH NOCREATEDB NOCREATEUSER ENCRYPTED PASSWORD E\'%s\'"' %
         (DB_USER, DB_PASS), user='postgres')
    sudo('psql -c "CREATE DATABASE %s WITH OWNER %s"' % (DB_DATABASE, DB_USER), user='postgres')
    # Restore database
    with cd('/opt/c4a_data_repository/Database'):
        run('psql -U %s -d %s < database' % (DB_USER, DB_DATABASE))


def _install_rest_api():
    """
    Install Rest API Interface in the server.

    :return:
    """
    with cd('/opt/c4a_data_repository/RestApiInterface/scripts'):
        run('/bin/bash ./install.sh')


def _install_linked_data():
    """
    Install Linked Data Interface in the server.

    :return:
    """
    with cd('/opt/c4a_data_repository/LinkedDataInterface/scripts'):
        run('/bin/bash ./install.sh')


# TODO WE NEED TO CHANGE THE BEHAVIOR OF THIS MAIN INSTALLATION METHOD.

# Main installation method.
def main_install():
    """
    Install entire project in the server:
            --> Project packages
            --> Deploy project and prepare virtualenv
            --> Create database user and restore data
            --> Install Rest API Interface
            --> Install Linked Data Interface
    :return:
    """
    # Call to every part of the program to install entire system.
    _install_deps()
    _deploy()
    _create_database()
    _install_rest_api()
    _install_linked_data()
