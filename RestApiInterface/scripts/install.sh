#!/bin/bash

# This script is fon installation purposes.

NGINX="/etc/nginx"



############# Control check

# Test you are in the current script dir
if [ ! -e "./install.sh" ]
then
  echo "Please cd into the scripts directory to run this script"
  exit 1
fi

# Test if you are root user
if [ "$(id -u)" != "0" ]; then
    echo "You need to run this script with sudo privileges"
    exit 1
fi

# Test if Nginx is installed in the system
if [ ! -d $NGINX ]; then
    echo "You don't have installed Nginx."
    exit 1
fi

# Test if there are all files ready to work
if [ ! -f $PWD/nginx_config/nginxCity4ageAPI ] || [ ! -f $PWD/systemd/city4ageAPI.service ] || [ ! -f $PWD/../ssl/nginx.crt ] || [ ! -f $PWD/../ssl/nginx.key ]
then
    echo "Some basic files are missing."
    exit 1
fi

################################## Main execution Script

#Create ssl directory
mkdir $NGINX/ssl
# Create new SSL CERTS
read -p "Do you want to create a new SSL CERT KEYS? " -n 1 -r
echo    # mew line
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout $NGINX/ssl/nginx.key -out $NGINX/ssl/nginx.crt
else
    # We are going to copy SSL certs from our SSL folder
    cp $PWD/../ssl/nginx.crt / $NGINX/ssl
    cp $PWD/../ssl/nginx.key / $NGINX/ssl
fi

######### Now we are going to open nginx_config and systemd files to changes PATHS to PWD --> dest
#todo
