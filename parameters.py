#!/usr/bin/python3
#
# parameters.py: contains all imported modules and global variables.
#
# Andrew Bishop
# 2021/11/13
#

# modules imported
"""
from functools import lru_cache
import hmac
import hashlib
import requests
import websocket
import threading
import json
from binance.client import Client
import csv
from urllib.parse import urlencode
import math
import os
import itertools
import pandas as pd
import numpy as np
import time
import pync
import curses
import sys
import shutil
import time
from pprint import pprint, pformat
from datetime import datetime

# my modules
from api import *
from backtest import *
from data_collection import *
from market import *
from setup import *
from trade import *
from websocket import *
"""

# global variables
BLUE    = '\u001b[1;38;5;$39m'
YELLOW  = '\u001b[38;5;$220m'
GREEN   = '\u001b[38;5;$46m'
GREY    = '\u001b[1;38;5;$8m'
RED     = '\033[1;31m'
WHITE   = '\033[0;37m'

PRIMARY_COLOR   = BLUE
SECONDARY_COLOR = GREY

#PARAM real(bool): True for real API, False for paper money
#RETURN none
#def init_api_keys(real=True):
global API_KEY, API_SECRET, BASE_URL

with open('keys.txt', 'r') as f:
    lines = f.readlines()
    #NOTE these are for the binance API
    #if real == False:
    #    API_KEY = lines[0][:-1]
    #    API_SECRET = lines[1][:-1]
    #    BASE_URL = "https://testnet.binance.vision"
    #elif real == True:
    API_KEY = lines[3][:-1]
    API_SECRET = lines[4][:-1]
    BASE_URL = "https://api.binance.com"
