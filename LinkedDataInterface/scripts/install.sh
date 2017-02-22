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
CONFIG="/etc/""${TOMCAT_VERSION}""/"
SERVER_CONFIG_FILE="/etc/""${TOMCAT_VERSION}""/server.xml"


# Path related variables
MAINFOLDER=`cd .. ; pwd`    # Mainfolder or the LinkedDataInterface
D2RQ="${MAINFOLDER}""/src/d2rq"
MAPPING="${MAINFOLDER}""/conf/mapping.ttl"
RULES="${MAINFOLDER}""/conf/rules.txt"

# Java jar file and System configuration file paths
#RULEREASONERFOLDER=$MAINFOLDER/src/ruleEngine/out/artifacts/ruleEngine_jar
SYSTEMDFILE=$MAINFOLDER/scripts/systemd/city4ageRuleEngine.service
SYSTEMDDESTINATIONFILE="/etc/systemd/system/city4ageRuleEngine.service"

# Fuseki main folder path
FUSEKI="${MAINFOLDER}""/src/fuseki"


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

# Test if OpenJDK 8 is installed in the system
if [ ! -d /usr/lib/jvm/java-8-openjdk-amd64 ]; then
    echo "Is OpenJDK8-jre installed in your system?"
    exit 1
fi

# Test if exist d2rq mapping.ttl file
if [ ! -f $MAPPING ]; then
    echo "Do you create mapping.ttl file and put in WE-INF?"
    exit 1
fi

# Test if exist a rules.txt file.
if [ ! -f $MAPPING ]; then
    echo "Do you create mapping.ttl file and put in WE-INF?"
    exit 1
fi

# Test if exist fuseki folder.

if [ ! -d $FUSEKI ]; then
    echo "Your fuseki installation in scripts folders doesn't exist"
    exit 1
fi


############### Main script execution
# Open mapping.ttl file to edit some values
echo "We are going to open 'mapping.ttl' file to edit some values..........."
sleep 3
nano $MAPPING 3>&1 1>&2 2>&3

# Move war file to tomcat dest
sudo rm -r $WEBAPPS/ROOT
sudo cp $FUSEKI/ROOT.war $WEBAPPS

echo "Creating fuseki configuration directory"
# Creating fuseki libs
if [ ! -d "/etc/fuseki" ]; then
    sudo mkdir "/etc/fuseki"
    sudo chown -R tomcat8:tomcat8 "/etc/fuseki"
fi
sleep 1
# Copy needed files into fuseki configuration folder
sudo /bin/cp -R $FUSEKI/run/configuration /etc/fuseki
sudo /bin/cp $FUSEKI/run/shiro.ini /etc/fuseki
echo "Fuseki files and cofigurations copied"
sleep 3

# Copy Libs

#echo "Copying jar files to Tomcat/lib installation"
#for data in `find $D2RQ/lib -name '*.jar'`;
#do
#    # If there are jar files, we will copy into Tomcat dir
#    sudo /bin/cp $data $LIB
#done


# Copy server.xml config File
sudo /bin/cp $MAINFOLDER/conf/tomcat/server.xml $CONFIG
sudo /bin/cp $MAINFOLDER/conf/tomcat/.keystore $HOME


# We want to add current .keystore path into server.xml
sudo sed "s+HOME+$HOME+g" $SERVER_CONFIG_FILE > $TFILE && sudo mv $TFILE $SERVER_CONFIG_FILE

# Restarting tomcat SERVER
echo "Starting Tomcat service................."
sudo service $TOMCAT_VERSION restart
echo "Data interface installed successfully!!!!!"
sleep 2

# Configure Rule Engine and install Celery service
printf "\n"

# Open rule file and edit,
echo "We are going to open 'rules.txt' file to edit some values..........."
sleep 3
nano $RULES 3>&1 1>&2 2>&3
sleep 2

# Change old text with Path of the projecs' mainfolder and copy to DestFile
sudo sed "s+$OLD+$MAINFOLDER+g" "$SYSTEMDFILE" > $TFILE && sudo mv $TFILE $SYSTEMDDESTINATIONFILE
sudo chmod +x $SYSTEMDDESTINATIONFILE

# Launch daemon-reload and start unit target.
echo "Reloading daemons and activating RuleEngineReasoner........"
sudo systemctl daemon-reload
sudo systemctl start city4ageRuleEngine.service
sudo systemctl enable city4ageRuleEngine.service
echo "Service unit file installed and activated!!"

exit 0