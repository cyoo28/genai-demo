#!/bin/bash
# create the tunnel
# gcloud compute ssh ix-pub --tunnel-through-iap -- -L 3306:10.16.192.3:3306

# Script to start web server hosted in GCP.
# Assumes the venv is in ~/env/vertex
# Assumes the webapp .py is in ~/genai-demo

VENV=~/env/vertex
APP_HOME=~/genai-demo

if [ ! -d $VENV ]; then
    echo "Virtual env not found: $VENV"
    exit 1
elif [ ! -d $APP_HOME ]; then
    echo "Webapp home not found: $APP_HOME"
    exit 1
fi

echo "Activating virtual env: $VENV/bin/activate"
. $VENV/bin/activate

echo "Running app"
cd $APP_HOME
export GCPPROJECT=ix-sandbox
export GCPREGION=us-central1
#export DBHOST=localhost
export DBHOST=127.0.0.1
export FLASK_APP=genai_webapp
flask run

deactivate