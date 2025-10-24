#!/bin/bash
#
# Set variables for the virtual environment and webapp directory
# Assumes the venv is in ~/env/bedrock
# Assumes the webapp .py is in ~/genai-demo
VENV=~/env/bedrock
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
if [[ "$(curl -s --connect-timeout 1 -o /dev/null -w '%{http_code}'\
    http://169.254.169.254/latest/meta-data/)" != "200" ]]; then
    echo "Not on EC2 — setting AWSPROFILE and DBHOST"
    export AWSPROFILE=ix-dev
    export DBHOST=127.0.0.1
else
    echo "On EC2 - not setting AWSPROFILE and DBHOST"
fi
export AWSREGION=us-east-1
# Run the webapp
echo "Running app"
cd $APP_HOME
# Run using Waitress on port 8080
python -m waitress --host=0.0.0.0 --port=8080 genai_webapp:app
deactivate