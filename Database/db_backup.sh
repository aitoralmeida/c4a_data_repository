#!/usr/bin/env bash

#################################################################
########
########       This script makes a database backup every day and removes
########       Old backups
########
#################################################################

# We set the database user, password and name
DBUSER="city4agedb"
DBPASSWORD="city4agedb"
DATABASE="city4agedb"
TIME=`date +%Y-%m-%d_%T`
FILENAME="city4age-database.$TIME.backup"
BACKUPFOLDER="/opt/city4age_database_backups"

############# Control check
# check if there is a database installed in the system
if [[ ! $(dpkg -l | grep -E '^ii' | grep postgresql) ]]; then
    echo "You must have installed a PostgreSQL database into the system"
    exit 1
fi

# Check if there is a backup folder created. Otherwise the script creates one.
# Test if Nginx is installed in the system
if [ ! -d  $BACKUPFOLDER ]; then
    # We create the backup folder
    mkdir -p "$HOME/city4age_database_backups"
fi

############# Creating backup
# Setting the password in env
export PGPASSWORD=$DBPASSWORD

# Check if the database exist into the system

if [[ $(psql -lqt -U $DBUSER | cut -d \| -f 1 | grep -w $DATABASE | wc -l) -eq 0 ]]; then
    echo "The database does not exist"
    exit 1
fi

# Create the backup of the database in /temp file
/usr/bin/pg_dump --host localhost --port 5432 --username $DBUSER --role $DBUSER --no-password  --format tar --blobs --section pre-data --section data --section post-data --verbose --file "/tmp/$FILENAME" $DATABASE
echo "Database copy created"
# Move the dump to backup folder
/bin/cp /tmp/$FILENAME $BACKUPFOLDER

############# Cleaning tool
# Find and delete the las 7 previous days copies
find $BACKUPFOLDER -mtime +7 -type f -delete

exit 0
