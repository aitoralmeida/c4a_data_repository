from fabric.api import run, env, sudo
from fabric.context_managers import cd



####################################
####################################
######### Set servers information

env.hosts = [
    '10.48.1.49',
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

_main_install = False

def _deploy():
    """
    Deploy all city4age project in a destination directory.

    :return:
    """
    run('mkdir /home/city4age/fabricTest')
    with cd('/home/city4age/'):
        run('git clone https://elektro108@bitbucket.org/elektro108/c4a_data_infrastructure.git')


def install_rest_api():
    """
    Install Rest API Interface in the server.

    :return:
    """
    global _main_install
    if not _main_install:
        _deploy()
    with cd('/home/city4age/c4a_data_infrastructure/RestApiInterface/scripts'):
        # todo sudo(nlanlanlalnl)
        run('/bin/bash ./install.sh')


def install_linked_data():
    """
    Install Linked Data Interface in the server.

    :return:
    """
    global _main_install
    if not _main_install:
        _deploy()
    with cd('/home/city4age/c4a_data_infrastructure/LinkedDataInterface/scripts'):
        sudo('/bin/bash ./install.sh')


def main_installation():
    """
    Install entire project in the server:
            --> Rest API Interface
            --> Linked Data Interface
    :return:
    """
    # We ask to user the name of the current user of the machine and we make the connection
    print "The current username is : %s" % env.user
    global _main_install
    _main_install = True
    _deploy()
    #install_rest_api()
    #install_linked_data()
