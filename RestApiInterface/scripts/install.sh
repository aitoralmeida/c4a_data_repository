#!/bin/bash

#################################################################
########
########       Install script
########
########       The goal of this script is to install all REST API interface
########       in the system and use the path of the current installed project directory.
########
########
#################################################################


############ Nginx destination path
NGINX="/etc/nginx"

########### Instalation parameteres
TFILE="/tmp/out.tmp.$$"

# Main folder of the project.
MAINFOLDER=`cd .. ; pwd`    # MainFolder of the RestAPiInterface
# Source folders
NGINXCONFIGFILE=$PWD/nginx_config/nginxCity4ageAPI
SYSTEMDCONFILE=$PWD/systemd/city4ageAPI.service
# Destination folders
NGINXDESTFILE=$NGINX/sites-available/nginxCity4ageAPI
SYSTEMDDESTFILE="/etc/systemd/system/city4ageAPI.service"
# Text to be replaced (this text is inside config files)
OLD="<project path>"

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
if [ ! -f $PWD/nginx_config/nginxCity4ageAPI ] || [ ! -f $PWD/systemd/city4ageAPI.service ] || [ ! -f $MAINFOLDER/ssl/nginx.crt ] || [ ! -f $MAINFOLDER/ssl/nginx.key ]
then
    echo "Some basic files are missing."
    exit 1
fi

# Test if rest_api.cfg exists.
if [ ! -f $MAINFOLDER/conf/rest_api.cfg ]
then
    echo "It seems that you don't have any Rest Api configuration file under conf folder"
fi

################################## Main execution Script
echo "We are going to open database conf file to edit database connection parameters"
slepp 4
nano "$MAINFOLDER/conf/rest_api.cfg" 3>&1 1>&2 2>&3

#Create ssl directory
[ ! -d $NGINX/ssl ] && mkdir -p $NGINX/ssl || :
# Create new SSL CERTS
read -p "Do you want to create a new SSL CERT KEYS? " -n 1 -r
echo    # mew line
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "We are going to copy SSL certs from our SSL folder........"
    /bin/cp $MAINFOLDER/ssl/nginx.crt $NGINX/ssl
    /bin/cp $MAINFOLDER/ssl/nginx.key $NGINX/ssl
    echo "Files copied successfully!!!"
else
    echo "Creating new pair of keys................................."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout $NGINX/ssl/nginx.key -out $NGINX/ssl/nginx.crt
    echo "Done!"
fi

# Copy Systemd unit file, modify paths and start it
if [ -f $SYSTEMDCONFILE -a -r $SYSTEMDCONFILE ]; then
    # Change old text with Path of the projecs' mainfolder and copy to DestFile
    sed "s+$OLD+$MAINFOLDER+g" "$SYSTEMDCONFILE" > $TFILE && mv $TFILE $SYSTEMDDESTFILE
    chmod 664 $SYSTEMDDESTFILE
    echo "uWSGI unit file installed succesfully!!"
    echo "We are going to reload systemd unit files and activate our new unit"
    # Launch daemon-reload and start uWSGI service
    systemctl daemon-reload
    systemctl start city4ageAPI.service
    systemctl enable city4ageAPI.service
    echo "Service unit file installed and activated!!"
else
    echo "Error: Cannot read $SYSTEMDCONFILE"
    exit 1
fi

# Copy Nging config file and replace with configuration paths
if [ -f $NGINXCONFIGFILE -a -r $NGINXCONFIGFILE ]; then
    # Change old text with Path of the projecs' mainfolder and copy to DestFile
    sed "s+$OLD+$MAINFOLDER+g" "$NGINXCONFIGFILE" > $TFILE && mv $TFILE $NGINXDESTFILE
    # Generate a symlink to enable our new config to nginx
    ln -s $NGINXDESTFILE $NGINX/sites-enabled
    # delete default symlink (avoid some problems)
    rm $NGINX/sites-enabled/default
    echo "Nginx config file installed succesfully!!"
    echo "Attemping to restart the server........"
    service nginx restart
else
    echo "Error: Cannot read $NGINXCONFIGFILE"
    exit 1
fi
