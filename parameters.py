#!/usr/bin/python3
#
# parameters.py: contains all imported modules and global variables.
#
# Andrew Bishop, Ryan Manak
# 2021/11/13
#

# modules imported
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
from pprint import pprint, pformat
from datetime import datetime


# global variables
BLUE    = '\u001b[1;38;5;$39m'
YELLOW  = '\u001b[38;5;$220m'
GREEN   = '\u001b[38;5;$46m'
GREY    = '\u001b[1;38;5;$8m'
RED     = '\033[1;31m'
WHITE   = '\033[0;37m'

PRIMARY_COLOR   = BLUE
SECONDARY_COLOR = GREY

