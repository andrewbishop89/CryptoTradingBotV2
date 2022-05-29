#!/usr/bin/python3
#
# main_coordinator.py: executes the method specified from the system arguments 
# or the internal variables.
#
# Andrew Bishop
# 2022/05/11
#

import sys
import logging
from methods.method_2.main_2 import main
from helper_functions.market import *

if __name__ == "__main__":
    logger = logging.getLogger("main")
    LOGGING_LEVEL = logging.DEBUG

    logger.setLevel(LOGGING_LEVEL)

    #symbols = ["BTCUSDT", "ADAUSDT", "ETHUSDT", "TRXUSDT", "SOLUSDT", "LTCUSDT", "XRPUSDT", "XMRUSDT", "DOTUSDT"]
    #symbols = top_gainers(2).index#[-25:]
    num_symbols = int(sys.argv[1]) if (len(sys.argv) > 1) else 50
    symbols = top_volume_gainers(num_symbols).index
    #symbols = symbols.drop_duplicates()

    main(symbols, 12)