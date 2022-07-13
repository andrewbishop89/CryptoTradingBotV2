#!/usr/bin/python3
#
# .py: 
#
# Andrew Bishop
# 2022/07/08
#

from typing import Callable, Tuple, List, Any, Dict
from helper_functions.data_collection import download_recent_klines
from helper_functions.trade import buy_trade, sell_trade
from multiprocessing import Pool
from dataclasses import dataclass
import logging
import time
import websockets
from websockets.client import WebSocketClientProtocol
import asyncio
import os
import importlib
from enum import Enum
import pandas as pd
from rich.pretty import pprint
from rich.console import Console

print = Console().print


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
    # METHOD PARAMETERS
    method_type: MethodType #real/paper/backtest
    kline_limit: int
    
    # BUY PARAMETERS
    trade_quote_quantity: float
    min_profit: float
    
    # SELL PARAMETERS
    risk_multiplier: float
    
    # TRADE CONDITIONS
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
    
    def __postinit__(self):
        self.trade_state = TradeState.buy
            
    def __call__(self, klines):
        return self.run(klines)
    
    def run(self, klines):
        
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


@dataclass
class SymbolStream:
    symbol: str
    stream: WebSocketClientProtocol


def generate_kline_set(symbols: List[str], intervals: List[str], limit: int=50) -> Dict[Tuple[str, str], pd.DataFrame]:
    """

    Args:
        symbols (List[str]): _description_
        intervals (List[str]): _description_
        limit (int, optional): _description_. Defaults to 50.

    Returns:
        Dict[Tuple[str, str], pd.DataFrame]: _description_
    """
    kline_sets = {}
    for interval in intervals:
        for symbol in symbols:
            kline_sets[(interval, symbol)] = download_recent_klines(
                symbol=symbol,
                interval=interval,
                limit=limit)
            
    return kline_sets
    
    
@dataclass
class TradeProcess:
    
    symbols: List[str]
    intervals: List[str]
    trade_info: TradeInfo
        
    def begin(self):
        return asyncio.run(self.async_begin())
        
    async def async_begin(self):
        
        # INITIALIZE TRADE INFORMATION
        method_type = self.trade_info.method_type
        
        buy_conditions = self.trade_info.buy_conditions
        sell_conditions = self.trade_info.sell_conditions
        
        klines = generate_kline_set(self.symbols, self.intervals, trade_info.limit)
        
        streams = {}
        
        # INITIALIZE STREAMS
        
        #TODO add `limit` amount of klines to beginning of stream kline from download recent klines 
        #TODO change for loop to a map
        for interval in self.intervals:
            for symbol in self.symbols:
                ws_path = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@kline_{interval}"
                streams[(symbol, interval)] = await websockets.connect(ws_path)
        
        for stream in streams.values():
            time.sleep(1)
            print(stream, stream.open, "\n", await stream.recv(), "\n")
            
        trade_cycles = list(map(TradeCycle, self.symbols))
        
        pprint(trade_cycles)
        
        exit(1)
        
        while True:
            
            #TODO cycle through each coin and perform tests
            for trade_cycle in trade_cycles:
                
                #TODO download klines during each cycle (perhaps create dataclass for klines, need to sort by intervals)
                    #TODO check stream status when downloading data
                
                #TODO should return trade state on function call, if sell then only focus on that coin (if not unlimited)
                    #TODO perhaps make function call async so we can download klines in the meantime
                
                return
                
            
    
            
        
    
    
    

if __name__ == "__main__":
    
    # MAIN PARAMETERS
    method_index = 3
    method_type = MethodType.paper
    buy_parameters = ""
    sell_parameters = ""
    symbols = [ "BTCUSDT", "ADAUSDT", "TRXUSDT", "ETHUSDT" ]
    
    # ---------------
    
    method_file_path = ".".join(["methods", f"method_{method_index}"])
    method_file = __import__(method_file_path, fromlist=["buy_conditions", "sell_conditions"])
    # method_file = importlib.import_module(method_file_path)
    
    logger = get_logger()
        
    trade_info = TradeInfo(
        method_type=method_type,
        buy_parameters=buy_parameters,
        sell_parameters=sell_parameters,
        buy_conditions=method_file.buy_conditions,
        sell_conditions=method_file.sell_conditions
    )
    
    # trade_cycles = list(map(lambda symbol: TradeCycle(
    #     symbol=symbol,
    #     trade_info=trade_info
    #     ), symbols))
    

    # pprint(trade_cycles)
    # print(symbols)
    
    # cpu_count = os.cpu_count()
    # logger.info(f"Initializing Pool with {cpu_count} processes.")
    # time.sleep(0.5)
    # print(f"Initializing Pool with {cpu_count} processes.")
    # while True:
    #     for trade_cycle in trade_cycles:
    #         (lambda trade_cycle: trade_cycle.run())(trade_cycle)
    #     print("Sleeping for 2.")
    #     time.sleep(2)
    
trade_process = TradeProcess(symbols, ["5m", "1h"], trade_info)
trade_process.begin()

                
        
        
    
    
    
    
    