#!/usr/bin/python3
#
# method_2_func.py: contains functions for method 2 of crypto bot version 2.
#
# Andrew Bishop
# 2022/03/08
#

import threading
import time
import os
import logging

from helper_functions.data_collection import *
from helper_functions.market import *
from helper_functions.trade import *
from helper_functions.analysis import *
from constants.parameters import *
from methods.method_2.method_2_backtest import *

logger = logging.getLogger("main")

#----------------------------------functions-----------------------------------

def get_profits() -> pd.DataFrame:
    """
    Description:
        Returns DataFrame of the most recent profit logs.
    """
    return pd.read_csv(os.path.join("logs", "profits.csv"))


def display_all_profits():
    """
    Description:
        Prints all recent profit information to the screen.
    """
    profits = get_profits()
    print(f"PROFIT: {round(sum(profits.iloc[:, 0]),2)}%")
    print(profits.iloc[:, 0].describe())
    print(profits.iloc[:, 0][profits.iloc[:, 0] > 0].describe())
    print(profits.iloc[:, 0][profits.iloc[:, 0] < 0].describe())
    print(profits.iloc[:, 1][profits.iloc[:, 0] > 0].describe())
    print(profits.iloc[:, 1][profits.iloc[:, 0] < 0].describe())


def display_loss(symbol: str, profit_index: int, profit: float):
    """
    Description:
        Prints trade loss on the screen.
    Args:
        symbol (str): symbol of coin traded.
        profit_index (int): index of profit trade.
        profit (float): profit during trade.
    """
    print(f"\t{symbol} LOSS:".ljust(30) + \
          f"{RED if (profit_index < 2) else GREY}" + \
          f"{'{:.4f}'.format(profit*100)}%{WHITE}")


def display_profit(symbol: str, profit_index: int, profit: float):
    """
    Description:
        Prints trade profit on the screen.
    Args:
        symbol (str): symbol of coin traded.
        profit_index (int): index of profit trade.
        profit (float): profit during trade.
    """
    print(f"\t{symbol} PROFIT {profit_index}:".ljust(30) + \
          f"{GREEN}{'{:.4f}'.format(profit*100)}%{WHITE}")


def init_logs():
    """
    Description:
        Moves the previous profits to a new file and clears the profits.csv 
        file.
    """
    with open(os.path.join("logs", "profits.csv"), "r") as f:
        old_logs = f.read()
    with open(os.path.join("logs", "profits.csv"), "w") as f:
        f.write("profit,symbol,buy_price,sell_price,buy_time," + \
            "sell_time,side,profit_split_ratio,std_5m,difference_1h," + \
            "price_24h,volume_24h,volume_rel,risk_multiplier,\n")
    index = 1
    fp = os.path.join("logs", f"profits_{index}.csv")
    while os.path.isfile(fp):
        index += 1
        fp = os.path.join("logs", f"profits_{index}.csv")
    with open(fp, "w") as f:
        f.write(old_logs)        


def log_profits(
        profit, 
        symbol: str, 
        buy_price, 
        sell_price, 
        buy_time, 
        sell_time, 
        side, 
        profit_split_ratio, 
        std_5m, 
        difference_1h,
        price_24h,
        volume_24h,
        volume_rel,
        risk_multiplier,
        min_price,
        max_price,
        max_profit,
        max_stop,
        potential_profit,
        file_lock: threading.Lock, 
        real: bool=False):
    """
    Description:
        Logs the data of the trade specified in the arguments.
    Args:
        profit (_type_): profit in trade.
        symbol (str): symbol in trade.
        buy_price (_type_): buy price in trade.
        sell_price (_type_): sell price in trade.
        buy_time (_type_): buy time in trade.
        sell_time (_type_): sell time in trade.
        side (_type_): side in trade.
        profit_split_ratio (_type_): profit split ratio in trade.
        std_5m (_type_): std of 5m candles in trade.
        difference_1h (_type_): difference of 1h EMA in trade.
        price_24h (_type_): 24h price ticker of symbol in trade.
        volume_24h (_type_): 24h volume of symbol.
        volume_rel (_type_): current 1h volume * 24 / 24h volume.
        risk_multiplier (_type_):
        file_lock (threading.Lock): file lock for threading
        real (bool, optional): True for real money and False otherwise
        (defaults to False)
    """
    file_lock.acquire()
        
    year = datetime.utcfromtimestamp(time.time()-7*3600).strftime('%Y')
    month = datetime.utcfromtimestamp(time.time()-7*3600).strftime('%B')

    today_filename = datetime.utcfromtimestamp(time.time()-7*3600).strftime('%m_%d_%y')
    if real:
        fp = os.path.join("logs", "real_money", year, month, f"{today_filename}.csv")
    else:
        fp = os.path.join("logs", "paper_money", year, month, f"{today_filename}.csv")
        
    confirmed_fp = "logs"
    walk = fp.split(fp[4])
    for d in walk[1:-1]:
        confirmed_fp = os.path.join(confirmed_fp, d)
        if not os.path.isdir(confirmed_fp):
            os.mkdir(confirmed_fp)

    fp = os.path.join(confirmed_fp, walk[-1])
    if not os.path.isfile(fp):
        with open(fp, "w") as f:
            f.write("profit,symbol,buy_price,sell_price,buy_time," + \
                "sell_time,side,profit_split_ratio,std_5m," + \
                "difference_1h,price_24h,volume_24h,volume_rel," + \
                "risk_multiplier,min_price,max_price,max_profit,max_stop,potential_profit\n")
    with open(fp, "a") as f:
        f.write(f"{profit},{symbol},{buy_price},{sell_price}," + \
            f"{buy_time},{sell_time},{side},{profit_split_ratio}," + \
            f"{std_5m},{difference_1h},{price_24h},{volume_24h}," + \
            f"{volume_rel},{risk_multiplier},{min_price},{max_price},{max_profit},{max_stop},{potential_profit}\n")
    file_lock.release()