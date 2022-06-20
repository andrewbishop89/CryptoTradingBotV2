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
from typing import Tuple
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
    api_keys: threading.Lock = threading.Lock()
    profit_file: threading.Lock = threading.Lock()
    active_trade: threading.Lock = threading.Lock() if ("unlimited" not in sys.argv) else FakeLock()


@dataclass
class OrderCondition:
    func: Callable
    args: List

    def __call__(self):
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

    # UPDATE AND DOWNLOAD DATA
    def update_trade_data(self) -> pd.DataFrame:
        return

    # PRE TRADE STAGE
    def check_buy_condition_met(self, buy_Condition: TradeConditions) -> TradeReceipt:
        return

    # POST TRADE STAGE
    def check_sell_condition_met(self, sell_Condition: TradeConditions) -> TradeReceipt:
        return

    # RESET AND LOG STAGE
    def log_trade_data(self, trade_data: TradeData):
        return
