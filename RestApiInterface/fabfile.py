from fabric.api import run, env
from fabric.context_managers import cd


env.hosts = [
    '10.48.1.49',
  # 'ip.add.rr.ess
  # 'server2.domain.tld',
]

# Set the username
env.user = "city4age"
env.password = "city4age"   # TODO we must remove it


def install_script():
    with cd('/home/city4age/c4a_data_infrastructure/RestApiInterface/scripts'):
        run('/bin/bash ./install.sh')
