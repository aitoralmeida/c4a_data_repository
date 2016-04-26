#!/bin/bash

# This is a simple bash script to move all contents of WEB-INF/lib to --> /usr/sahe/tomcat7/lib
# This scripts avoid memory leaks in tomcat7 and makes the project more scalable.
# CAUTION!!!!!
# Use it only in a UBUNTU 14.04 GNU/LINUX distribution.


LIB="/var/lib/tomcat7/webapps/d2rq/WEB-INF/lib/"
TOMCAT7="/usr/share/tomcat7/lib"


# Test if you are root user
if [ "$(id -u)" != "0" ]; then
    echo "You need to run this script with sudo privileges"
    exit 1
fi

# Test if tomcat7 lib folder exists in the system
if [ ! -d $TOMCAT7 ]; then
    echo "Is tomcat7 installed in your system?"
    exit 1
fi

# Test if $LIB exist
if [ -d $LIB ] && [ "$(ls -A $LIB)" ]; then
     # Copy contents to Tomcat's lib
     for dest in `ls $LIB`
     do
        mv $LIB/$dest $TOMCAT7
     done
     echo "Libs copied successfully!!"
     # Restart tomcat server
     service tomcat7 restart
else
    echo "There isn't any installation of d2rq. Please make sure you have deployed anything in the system."
    exit 1
fi

exit 0
