#!/bin/bash

##############################################################################
##### This script creates war file and put in in Tomcat's webapp folder ready to start
##### This script is for Ubuntu 14.04 or 16.04 Instalations
##### Remember to configure env variables to know if you are goint to use tomcat7 or 8
#####
###############################################################################


TOMCAT_VERSION="tomcat7"


WEBAPPS="/var/lib/""${TOMCAT_VERSION}""/webapps/"
LIB="/usr/share/""${TOMCAT_VERSION}""/lib"


SOURCE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
D2RQ="${SOURCE}""/../src/d2rq"
MAPPING="${SOURCE}""/../src/d2rq/webapp/WEB-INF/mapping.ttl"


############# Control check

# Test you are in the current script dir
if [ ! -e "./copy_to_tomcat_lib.sh" ]
then
  echo "Please cd into the scripts directory to run this script"
  exit 1
fi

# Test if you are root user
if [ "$(id -u)" != "0" ]; then
    echo "You need to run this script with sudo privileges"
    exit 1
fi

# Test if tomcat lib folder exists in the system
if [ ! -d $LIB ]; then
    echo "Is ""${TOMCAT_VERSION}"" installed in your system?"
    exit 1
fi

# Test if exist d2rq mapping.ttl file
if [ ! -f $MAPPING ]; then
    echo "Do you create mapping.ttl file and put in WE-INF?"
    exit 1
fi

########### Start here main script

# we are going to create War file
echo "Creating war file.............................."
ant war -s $D2RQ
echo "War file created!!!"
# Copy war file to Tomcat dest
mv $D2RQ/d2rq.war $WEBAPPS
# Copy Libs
echo "Copying jar files to Tomcat/lib installation"
for data in `find $D2RQ/lib -name '*.jar'`;
do
    # If there are jar files, we will copy in Tomcat dir
    cp $data $LIB
done

echo "Starting Tomcat service................."
service $TOMCAT_VERSION restart
echo "Data interface installed successfully!!!!!"
exit 0
