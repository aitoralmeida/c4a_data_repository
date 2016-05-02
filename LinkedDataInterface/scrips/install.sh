#!/bin/bash

#################################################################
########
########       Install script
########
########       The goal of this script is to install all Linked Data Interface
########       in the system and use the path of the current installed project directory.
########
########
#################################################################

# Tomcat related variables
TOMCAT_VERSION="tomcat8"
LIB="/usr/share/""${TOMCAT_VERSION}""/lib"
WEBAPPS="/var/lib/""${TOMCAT_VERSION}""/webapps/"

# Path related variables
MAINFOLDER=`cd .. ; pwd`
D2RQ="${MAINFOLDER}""/src/d2rq"
MAPPING="${MAINFOLDER}""/src/d2rq/webapp/WEB-INF/mapping.ttl"

# Celery related variables
CELERY_DIR="/usr/bin/celery"
CELERYSCRIPTFILE=$MAINFOLDER/scrips/systemd/celery.sh
CELERYDESTFILE="/usr/local/bin/celery.sh"
TFILE="/tmp/out.tmp.$$"

# Text to be replaced (this text is inside config files)
OLD="<project path>"

############# Control check
# Test you are in the current script dir
if [ ! -e "./install.sh" ]; then
  echo "Please cd into the scripts directory to run this script"
  exit 1
fi

# Test if tomcat lib folder exists in the system
if [ ! -d $LIB ]; then
    echo "Is ""${TOMCAT_VERSION}"" installed in your system?"
    exit 1
fi

# Test if celery is installed in the system
if [ ! -d $CELERY_DIR ]; then
    echo "Is Python-Celery installed in your system?"
    exit 1
fi

# Test if RabbitMQ is installed in the system
if [ ! -d /usr/lib/rabbitmq/bin ]; then
    echo "Is RabbitMQ installed in your system?"
    exit 1
fi

# Test if OpenJDK 8 is installed in the system
if [ ! -d /usr/lib/jvm/java-8-openjdk-amd64 ]; then
    echo "Is OpenJDK8-jre iinstalled in your system?"
    exit 1
fi

# Test if exist d2rq mapping.ttl file
if [ ! -f $MAPPING ]; then
    echo "Do you create mapping.ttl file and put in WE-INF?"
    exit 1
fi

############### Main script execution
# Open mapping.ttl file to edit some values
echo "We are going to open 'mapping.ttl' file to edit some values..........."
sleep 3
nano "$MAINFOLDER/src/d2rq/webapp/WEB-INF/mapping.ttl" 3>&1 1>&2 2>&3

#todo copy this mapping file into ruleEngine to infer new statements
# /bin/cp $MAINFOLDER/src/d2rq/webapp/WEB-INF/mapping.ttl $MAINFOLDER/ruleEngine

# Create WAR FILE
if [ ! -f $D2RQ/d2rq.war ]; then
    echo "Creating war file.............................."
    ant war -s $D2RQ
    echo "War file created!!!"
fi
# Move war file to tomcat dest
sudo mv $D2RQ/d2rq.war $WEBAPPS
# Copy Libs
echo "Copying jar files to Tomcat/lib installation"
for data in `find $D2RQ/lib -name '*.jar'`;
do
    # If there are jar files, we will copy into Tomcat dir
    sudo /bin/cp $data $LIB
done

echo "Starting Tomcat service................."
sudo service $TOMCAT_VERSION restart
echo "Data interface installed successfully!!!!!"
sleep 2

# Configure Rule Engine and install Celery service
printf "\n"
echo "Installing celery service..............."

# Open rule file and edit,
echo "We are going to open 'rules.txt' file to edit some values..........."
sleep 3
nano "$MAINFOLDER/ruleEngine/rules.txt" 3>&1 1>&2 2>&3

# Copy Celery script and modify Paths
if [ -f $CELERYSCRIPTFILE -a -r $CELERYSCRIPTFILE ]; then
    # Change old text with Path of the projecs' mainfolder and copy to DestFile
    sed "s+$OLD+$MAINFOLDER+g" "$CELERYSCRIPTFILE" > $TFILE && sudo mv $TFILE $CELERYDESTFILE
    sudo chmod +x $CELERYDESTFILE
    # Copy systemd unit file and reload all
    echo "We are goingt o copy celery systemd service and activate it......"
    sleep 2
    sudo /bin/cp $MAINFOLDER/scrips/systemd/celery.service /etc/systemd/system
    # Launch daemon-reload and start uWSGI service
    echo "Reloading daemons and activating celery services........"
    sudo systemctl daemon-reload
    sudo systemctl start celery.service
    sudo systemctl enable celery.service
    echo "Service unit file installed and activated!!"
else
    echo "Error: Cannot read $CELERYSCRIPTFILE"
    exit 1
fi

exit 0