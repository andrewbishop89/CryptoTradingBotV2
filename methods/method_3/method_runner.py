#!/usr/bin/python3
#
# .py: 
#
# Andrew Bishop
# 2022/07/08
#

from typing import Callable, Tuple, List, Any
from helper_functions.trade import buy_trade, sell_trade
from multiprocessing import Pool
from dataclasses import dataclass
import logging
import os
from enum import Enum

@dataclass
class TestCondition:
    """
    A single test condition with a function returning a boolean and it's parameters.
    """
    _condition_func: Callable
    _parameters: List[Any]

    def check(self, klines) -> bool:
        """Runs the TestCondition object's test and returns True if it passed and False otherwise."""
        return self._function(klines, *self._parameters)


@dataclass
class TestConditions:
    """
    A list of all test conditions with their function and parameters.
    """
    _test_conditions: List[TestCondition]
    
    def check_all(self, klines):
        """Runs all TestCondtions and returns True if they all pass and False otherwise."""
        for test in self._test_conditions:
            if not test.run(klines):
                return False
        else:
            return True


@dataclass
class BuyParameters:
    """
    
    """
    quote_quantity: float
    risk_multiplier: float
    symbol: str
    
@dataclass
class SellParameters:
    """
    
    """


class MethodType(Enum):
    """

    """
    real = 0
    paper = 1
    backtest = 2
    
    
@dataclass
class TradeInfo:
    """
    
    """
    method_type: MethodType
    buy_parameters: BuyParameters
    sell_parameters: SellParameters
    buy_conditions: TestConditions
    sell_conditions: TestConditions

    
class TradeState(Enum):
    """Contains the current state of the trade cycle."""
    buy = 0         # no active trade, looking to buy in
    sell = 1        # active trade, looking to sell out
    wait = 2        # if other trades are active, wait


@dataclass
class TradeCycle:
    """
    Contains all information for a single trade cycle.
    """
    symbol: str
    trade_info: TradeInfo
    
    def __postinit__(self):
        self.trade_state = TradeState.buy
        self.method_type = self.trade_info.method_type
        
        self.buy_parameters = self.trade_info.buy_parameters
        self.sell_parameters = self.trade_info.sell_parameters
        
        self.buy_conditions = self.trade_info.buy_conditions
        self.sell_conditions = self.trade_info.sell_conditions
    
    
    def run(self):
        
        # TODO download klines
        klines = []
        
        # Check for buy-in
        if self.trade_state == TradeState.buy:
            if self.buy_conditions.check_all(klines):
                # TODO rewrite buy_trade function so it takes buy parameters object as argument
                buy_id, profit_quantity = buy_trade(self.buy_parameters)
                self.trade_state == TradeState.sell
            
        # Check for sell-out
        if self.trade_state == TradeState.sell:
            if self.sell_conditions.check_all(klines):
                # TODO rewrite sell_trade function so it takes buy parameters object as argument
                sell_id, _ = sell_trade(self.sell_parameters)            
                self.trade_state == TradeState.buy    
                
                # TODO implement logging here

def get_logger(logging_level=logging.INFO):
    logger = logging.getLogger(__name__)
    
    logger.setLevel(logging_level)
    log_fp = os.path.join("logs", f"{__name__}.log")
    handler = logging.FileHandler(log_fp, mode="a")
    formatter = logging.Formatter('%(levelname)s @ %(asctime)s - %(threadName)s - %(filename)s - Line %(lineno)d - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


if __name__ == "__main__":
    
    # MAIN PARAMETERS
    method_index = 3
    method_type = MethodType.paper
    buy_parameters = ""
    sell_parameters = ""
    symbols = [ "BTCUSDT" ]
    
    # ---------------
    
    method_file_path = os.path.join("methods", f"method_{method_index}")
    method_file = __import__(method_file_path)
    
    logger = get_logger()
        
    trade_info = TradeInfo(
        method_type=method_type,
        buy_parameters=buy_parameters,
        sell_parameters=sell_parameters,
        buy_conditions=method_file.buy_conditions,
        sell_conditions=method_file.sell_conditions
    )
    
    trade_cycles = list(map(lambda symbol: TradeCycle(
        symbol=symbol,
        trade_info=trade_info
        ), symbols))
    
    
    cpu_count = os.cpu_count()
    logger.info(f"Initializing Pool with {cpu_count} processes.")
    with Pool(cpu_count) as p:
        while True:
            p.map(lambda trade_cycle: trade_cycle.run(), trade_cycles)
        
        
        
    
    
    
    
    