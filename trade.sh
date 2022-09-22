#!/bin/sh

run_type=$1
method_index=2 #$2
MAIN_FILE=methods/method_2/main_$method_index.py

if [ -z "$run_type" ]; then 
  echo "Starting PAPER Method $method_index."
  python3 $MAIN_FILE $BINANCE_PAPER_KEY $BINANCE_PAPER_SECRET
elif [ "$run_type" == "real" ]; then
  echo "Starting REAL Method $method_index."
  python3 $MAIN_FILE $BINANCE_REAL_KEY $BINANCE_REAL_SECRET 
else
  echo "Error: Invalid run type specified in command line: '$run_type'"
  echo "Re-run with 'real' for real-money trading or no argument for paper-money trading."
  echo
  exit 1
fi

#TODO add default method to run if not specified 
#TODO add option for command line arguments to choose method
#TODO add option for command line arguments to choose paper or real

# Run Trade Method
echo "Finished Executing Method $method_index."
