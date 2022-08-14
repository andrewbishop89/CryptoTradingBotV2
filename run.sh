#!/bin/sh

# Check if keys file exists and create template if it does not
KEYS_FILE=constants/keys.sh
KEYS_TEMPLATE_FILE=constants/keys_template.sh

if [ ! -f "$KEYS_FILE" ]; then
	cp $KEYS_TEMPLATE_FILE $KEYS_FILE 
	echo "WARNING Keys file not found. Copying template to '$KEYS_FILE'.\n\nFill in your API keys and re-run."
	exit 1
fi

# Load constants
. ./constants/keys.sh

#TODO add default method to run if not specified 
#TODO add option for command line arguments to choose method
#TODO add option for command line arguments to choose paper or real

# Run Trade Method
python3 methods/method_runner.py
