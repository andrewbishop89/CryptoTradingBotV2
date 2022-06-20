#!/usr/bin/python3
#
# method_framework.py: contains all objects to create a new method.
#
# Andrew Bishop
# 2022/05/30
#

# modules imported
from dataclasses import dataclass
import sys
import threading
from typing import Callable, Tuple
import pync
import time
import os
import logging
from multiprocessing import Pool
from pprint import pprint, pformat

from helper_functions.data_collection import *
from helper_functions.market import *
from helper_functions.trade import *
from helper_functions.analysis import *
from helper_functions.websocket_func import *
from constants.parameters import *
from methods.method_2.method_2_backtest import *
from methods.method_2.method_2_func import *

logger = logging.getLogger("main")

# ----------------------------------functions-----------------------------------


# TODO tweak prettier autoformatter for no wrap text

@dataclass
class FakeLock:
    """Lock that doesn't do anything when referenced."""

    def locked(self):
        return False

    def acquire(self, timeout=None):
        return

    def release(self):
        return


@dataclass
class MethodLock:
    """
    Description:
        An object that contains all the threading locks for one method being run on separate threads.
        There is multiple trade cycle threads running the same method, thus this object holds the locks to avoid the thread collisions.
    Args:
        api_keys (threading.Lock):
        profit_file (threading.Lock):
        active_trade (threading.Lock):
    """
    api_keys: threading.Lock = threading.Lock()
    profit_file: threading.Lock = threading.Lock()
    active_trade: threading.Lock = threading.Lock() if ("unlimited" not in sys.argv) else FakeLock()


@dataclass
class OrderCondition:
    """
    Description:
        Contains a Callable and it's arguments as a list.
        This is one piece of criteria that is used for the program to determine whether it is currently the right time to buy in or sell out of a trade.
    Args:
        func (Callable): a function returning a boolean for the trade condition check
        args (List): a list of arguments for the above function to be called
    Returns:
        bool: returns true if the condition is met and false otherwise.
    """
    func: Callable
    args: List

    def __call__(self) -> bool:
        """
        Description:

        Returns:
            bool: 
        """
        return self.func(*self.args)


@dataclass
class TradeConditions:
    order_conditions: List[OrderCondition]

    def check_conditions(self):
        return all([condition() for condition in self.order_conditions])


@dataclass
class TradeData:
    def __init__(): return


@dataclass
class TradeReceipt:
    def __init__(): return


@dataclass
class TradeParameter:
    def __init__(): return


class Method:
    # list of symbols to run with method
    symbols: List[str]
    # list of parameters for trading
    trade_parameters: List[TradeParameter]
    # tuple of conditions (buy, sell)
    trade_conditions: Tuple[TradeConditions, TradeConditions]
    # object containing all locks
    method_lock: MethodLock = MethodLock()
    # list of symbols used as payment
    payment_symbols: List[str] = ["USDT", "BNB"]

    # PARAMETERS AND INITIALIZATION
    def __init__(self):

        # delete old data to clear up memory
        delete_old_data()

        # filter out invalid symbols if they exist
        self.symbols = filter(lambda x: x.endswith(
            tuple(self.payment_symbols)), self.symbols)

        # start all trade cycles
        for symbol in self.symbols:
            TradeCycle(symbol, self.trade_parameters)

        return


@dataclass
class TradeCycle:
    symbol: str
    trade_parameters: List[TradeParameter]

    # UPDATE AND DOWNLOAD DATA
    def update_trade_data(self) -> pd.DataFrame:
        return

    # PRE TRADE STAGE
    def check_buy_condition_met(self, buy_conditions: TradeConditions) -> TradeReceipt:
        return buy_conditions.check_conditions()

    # POST TRADE STAGE
    def check_sell_condition_met(self, sell_conditions: TradeConditions) -> TradeReceipt:
        return sell_conditions.check_conditions()

    # RESET AND LOG STAGE
    def log_trade_data(self, trade_data: TradeData):
        return

    # main trade cycle
    def __call__(self):

        trade_active = False
        while True:

            # update candle data and make sure streams are still alive
            self.update_trade_data()

            # if buy conditions ARE met and trade is NOT active then buy into trade
            if (not trade_active) and self.check_buy_condition_met():
                # TODO buy trade
                pass  

            # if sell conditions ARE met and trade IS active then sell out of trade
            if (trade_active) and self.check_sell_condition_met():
                # TODO sell trade
                pass  

                # log trade data
                self.log_trade_data()
