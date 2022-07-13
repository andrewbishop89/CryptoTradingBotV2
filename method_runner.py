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
import json
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
    
    def __post_init__(self):
        self.trade_state = TradeState.buy
    
    def run(self, klines: Dict[str, pd.DataFrame], buy_conditions: TestConditions, sell_conditions: TestConditions) -> TradeState:
        
        # Check for buy-in
        if self.trade_state == TradeState.buy:
            if buy_conditions.check_all(klines):
                # TODO rewrite buy_trade function so it takes buy parameters object as argument
                buy_id, profit_quantity = buy_trade(self.buy_parameters)
                self.trade_state == TradeState.sell
            
        # Check for sell-out
        if self.trade_state == TradeState.sell:
            if sell_conditions.check_all(klines):
                # TODO rewrite sell_trade function so it takes buy parameters object as argument
                sell_id, _ = sell_trade(self.sell_parameters)            
                self.trade_state == TradeState.buy
                
                # TODO implement logging here
                
        return self.trade_state
                
                
def format_kline(kline: dict) -> pd.DataFrame:
    """
    Converts kline from dict to dataframe.

    :param dict kline: dictionary of kline to be formatted
    :return pd.DataFrame: formatted kline dataframe
    """
    return pd.DataFrame(data={
        't': [int(kline['t']/1000)],
        'o': [float(kline['o'])],
        'c': [float(kline['c'])],
        'h': [float(kline['h'])],
        'l': [float(kline['l'])],
        'n': [float(kline['n'])],
        'v': [float(kline['v'])],
    }).set_index("t")


def get_logger(logging_level=logging.INFO):
    logger = logging.getLogger(__name__)
    
    logger.setLevel(logging_level)
    log_fp = os.path.join("logs", f"{__name__}.log")
    handler = logging.FileHandler(log_fp, mode="a")
    formatter = logging.Formatter('%(levelname)s @ %(asctime)s - %(threadName)s - %(filename)s - Line %(lineno)d - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def generate_kline_set(symbols: List[str], intervals: List[str], limit: int=50) -> Dict[Tuple[str, str], pd.DataFrame]:
    """
    Generates a dictionary containing the klines with keys as Tuple[str, str] where the strings are the symbol and interval respectively.

    :param List[str] symbols: list of symbols to download data for
    :param List[str] intervals: list of intervals to download data for
    :param int limit: amount of klines to download, defaults to 50
    :return Dict[Tuple[str, str], pd.DataFrame]: a set of downloaded klines sorted in dictionary form
    """
    kline_sets = {}
    for interval in intervals:
        for symbol in symbols:
            kline_sets[(symbol, interval)] = download_recent_klines(
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
        
        klines = generate_kline_set(self.symbols, self.intervals, trade_info.kline_limit)
        
        # INITIALIZE STREAMS
        
        streams = {}
        
        # connect stream for each symbol and interval pair
        for interval in self.intervals:
            for symbol in self.symbols:
                ws_path = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@kline_{interval}"
                print(f'Connecting "{symbol} {interval}" data stream...')
                streams[(symbol, interval)] = await websockets.connect(ws_path)

        trade_cycles = list(map(TradeCycle, self.symbols))
        
        while True:
            
            #TODO cycle through each coin and perform tests
            for trade_cycle in trade_cycles:
                
                # -------- DOWNLOAD DATA --------
                #TODO check stream status when downloading data
                
                # get iteration keys (symbol, interval) for stream and klines access
                current_keys = list(map(lambda interval: (trade_cycle.symbol, interval), self.intervals))
                
                # cycle through all keys
                for key in current_keys:
                    # from stream get latest kline
                    current_kline = format_kline(json.loads(await streams[key].recv())['k'])
                    # if last candles have equal time, update last candle of dataframe to latest kline from stream
                    if klines[key].iloc[-1].name == current_kline.iloc[-1].name:
                        klines[key] =  pd.concat([klines[key].iloc[:-1, :], current_kline])
                                        
                current_klines = {}
                for key in klines.keys():
                    if trade_cycle.symbol in key:
                        current_klines[key[1]] = klines[key]
                
                # -------- ANALYSIS --------
                #TODO should return trade state on function call, if sell then only focus on that coin (if not unlimited)
                
                # trade_cycle.run(current_klines, buy_conditions, sell_conditions) # not implemented yet
                
                
                #TODO perhaps make function call async so we can download klines in the meantime
                
            return
                
            
    
            
        
    
    
    

if __name__ == "__main__":
    
    # MAIN PARAMETERS
    method_index = 3
    method_type = MethodType.paper
    symbols = [ "BTCUSDT", "ADAUSDT", "TRXUSDT", "ETHUSDT" ]
    intervals = ["5m", "1m"]
    
    # ---------------
    
    method_file_path = ".".join(["methods", f"method_{method_index}"])
    method_file = __import__(method_file_path, fromlist=["buy_conditions", "sell_conditions"])
    
        
    trade_info = TradeInfo(
        method_type=method_type,
        kline_limit=21,
        trade_quote_quantity=10,
        min_profit=0.6,
        risk_multiplier=1.5,
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
    
trade_process = TradeProcess(symbols, intervals, trade_info)
trade_process.begin()

                
        
        
    
    
    
    
    