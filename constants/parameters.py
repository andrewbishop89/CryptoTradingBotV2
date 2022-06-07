#!/usr/bin/python3
#
# parameters.py: contains all API variables and other global variables.
#
# Andrew Bishop

import os
import json
import sys
from pprint import pprint, pformat
import logging

#------------------------------global-variables--------------------------------

BLUE    = '\u001b[1;38;5;$39m'
YELLOW  = '\u001b[38;5;$220m'
GREEN   = '\u001b[38;5;$46m'
GREY    = '\u001b[1;38;5;$8m'
RED     = '\033[1;31m'
WHITE   = '\033[0;37m'

PRIMARY_COLOR   = BLUE
SECONDARY_COLOR = GREY

#-------------------------------API-variables----------------------------------

global API_KEY, API_SECRET, BASE_URL #global so they are accessible everywhere

with open(os.path.join('constants', 'keys.json'), 'r') as f:
    keys = json.load(f)
    if "paper" in sys.argv:
        API_KEY = keys['binance_paper']['key']  # first line should be API key
        API_SECRET = keys['binance_paper']['secret']  # second line should be API secret    
    else:
        API_KEY = keys['binance_real']['key']  # first line should be API key
        API_SECRET = keys['binance_real']['secret']  # second line should be API secret
    BASE_URL = "https://api.binance.com"  # binance API base url

#------------------------------------------------------------------------------

logger = logging.getLogger("main")

# Logging Levels
# - DEBUG
# - INFO
# - WARNING
# - ERROR
# - CRITICAL

logger.setLevel(logging.INFO)
log_fp = os.path.join("logs", "main.log")
handler = logging.FileHandler(log_fp, mode="w")
formatter = logging.Formatter('%(levelname)s @ %(asctime)s - %(threadName)s - %(filename)s - Line %(lineno)d - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)
