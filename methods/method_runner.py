#!/usr/bin/python3
#
# .py: 
#
# Andrew Bishop
# 2022/07/08
#

from typing import Callable, Tuple, List, Any
from multiprocessing import Pool
from dataclasses import dataclass
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
    _symbol: str
    _trade_state: TradeState
    _buy_parameters: BuyParameters
    
    _buy_conditions: TestConditions
    _sell_conditions: TestConditions        


def main(
        method_index: int,
        quote_quantity: float,
        symbols: list
    ):

    method_active = True
    
    while method_active:
        
        trade_cycles = list(map())
        
        with Pool() as p:
            p.map()
    
    
    
    
    
    
    
    
    
    