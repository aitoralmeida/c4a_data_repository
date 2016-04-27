#!/bin/bash

# This file is for Ubuntu 16.04 only. It is a basic shell script.

CELERY_APP="task"
CELERY_CHDIR="/home/deusto/PycharmProjects/c4a_data_infrastructure/LinkedDataInterface/src/packCelery"
CELERY_NODES="task"

CELERY_LOG_DIR="/var/log/celery"
CELERY_RUN_DIR="/var/run/celery"
CELERY_LOG_FILE=celery-worker-%n.log
CELERY_PID_FILE=celery-worker-%n.pid

CELERY_LOG_LEVEL="INFO"

# Crete Celery user and Group with permissions
USER=root
GROUP=root


start() {
    # Create LOG and RUN DIR.
    if [ ! -d "CELERY_LOG_DIR" ]; then
        mkdir -p "$CELERY_LOG_DIR"
        chown "$USER":"$GROUP" "$CELERY_LOG_DIR"
    fi

    if [ ! -d "CELERY_RUN_DIR" ]; then
        mkdir -p "$CELERY_RUN_DIR"
        chown "$USER":"$GROUP" "$CELERY_RUN_DIR"
    fi

    # Launch celery
    /usr/bin/celery multi start "$CELERY_NODES" \
                                --pidfile="$CELERY_RUN_DIR/$CELERY_PID_FILE" \
                                --logfile="$CELERY_LOG_DIR/$CELERY_LOG_FILE" \
                                --loglevel="$CELERY_LOG_LEVEL" \
                                --app="$CELERY_APP" \
                                --workdir="$CELERY_CHDIR" \
                               --uid=$USER \
                               --gid=$GROUP \
				               --beat

    echo "Celery service started successfully"
}

# STOP
stop() {
    # Stop celery service
    /usr/bin/celery multi --verbose stop "$CELERY_NODES" \
                                --pidfile="$CELERY_RUN_DIR/$CELERY_PID_FILE" \
                                --logfile="$CELERY_LOG_DIR/$CELERY_LOG_FILE" \
                                --loglevel="$CELERY_LOG_LEVEL" \
                                --app="$CELERY_APP" \
                                --workdir="$CELERY_CHDIR" \
                                --uid=$USER \
                                --gid=$GROUP \
                                --beat
    echo "Celery service stopped"
}

case $1 in
  start|stop) "$1" ;;
esac
