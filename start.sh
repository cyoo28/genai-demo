#!/bin/bash

# Set variables for the virtual environment and webapp directory
# Assumes the venv is in ~/env/vertex
# Assumes the webapp .py is in ~/genai-demo
VENV=~/env/vertex
APP_HOME=~/genai-demo
# Check that the virtual environment exists
if [ ! -d $VENV ]; then
    echo "Virtual env not found: $VENV"
    exit 1
elif [ ! -d $APP_HOME ]; then
    echo "Webapp home not found: $APP_HOME"
    exit 1
fi
# Activate the environment
echo "Activating virtual env: $VENV/bin/activate"
. $VENV/bin/activate
# Export environment variables
# Only export AWSPROFILE if running on local machine
echo "Setting environment variables"
if [[ "$(curl -s -o /dev/null -w '%{http_code}' -H 'Metadata-Flavor: Google' \
    http://169.254.169.254/computeMetadata/v1/)" != "200" ]]; then
    echo "Not on GCE — setting GCPPROJECT and DBHOST"
    export GCPPROJECT=ix-sandbox
    export DBHOST=127.0.0.1
else
    echo "On GCE - not setting GCPPROJECT and DBHOST"
fi
export GCPREGION=us-central1
# Run the webapp
echo "Running app"
cd $APP_HOME
# Run using Waitress on port 8080
python -m waitress --host=0.0.0.0 --port=8080 genai_webapp:app
deactivate