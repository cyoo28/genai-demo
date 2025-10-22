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
if ! curl -s --connect-timeout 1 http://169.254.169.254/latest/meta-data/ >/dev/null; then
    export AWSPROFILE=ix-dev
fi
export AWSREGION=us-east-1
export DBHOST=127.0.0.1
# Run the webapp
echo "Running app"
cd $APP_HOME
# Run using Waitress on port 5000
python -m waitress --host=0.0.0.0 --port=5000 genai_webapp:app
deactivate