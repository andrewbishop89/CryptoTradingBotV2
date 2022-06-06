#!/usr/bin/python3
#
# main_coordinator.py: executes the method specified from the system arguments 
# or the internal variables.
#
# Andrew Bishop
# 2022/05/11
#
# Crontab:
# @reboot sleep 60 && cd ~/CryptoTradingBotV2 && /Library/Frameworks/Python.framework/Versions/3.8/bin/python3 ~/CryptoTradingBotV2/main_coordinatory.py >> ~/CryptoTradingBotV2/logs/cron_logs.log 2>&1
#

import sys
import logging
from methods.method_2.main_2 import main
from helper_functions.market import *

if __name__ == "__main__":
    logger = logging.getLogger("main")
    LOGGING_LEVEL = logging.INFO

    logger.setLevel(LOGGING_LEVEL)

    #symbols = ["BTCUSDT", "ADAUSDT", "ETHUSDT", "TRXUSDT", "SOLUSDT", "LTCUSDT", "XRPUSDT", "XMRUSDT", "DOTUSDT"]
    #symbols = top_gainers(2).index#[-25:]
    num_symbols = int(sys.argv[1]) if (len(sys.argv) > 1) else 50
    symbols = top_volume_gainers(num_symbols).index
    #symbols = symbols.drop_duplicates()

    try:
        main(symbols)
    except KeyboardInterrupt as e:
        logger.error(f"Keyboard Interrupt raised in main. Thread Count: {threading.active_count()}", exc_info=True)
        print("\nFinishing Program.")
        sys.exit()
        
        