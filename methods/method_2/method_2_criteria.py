#!/usr/bin/python3
#
# method_2_criteria.py: contains functions for method 2 buy in criteria of 
# crypto bot version 2.
#
# Andrew Bishop
# 2022/03/10
#
#

# modules imported
import sys
import threading
import pync
import time
import os
from multiprocessing import Pool
from pprint import pprint

from data_collection import *
from market import *
from trade import *
from analysis import *
from parameters import *
from method_2_backtest import *
from method_2_func import *