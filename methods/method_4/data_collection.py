"""

"""
from binance.client import Client
import pandas as pd

from functions.setup.setup import retrieve_keys
from classes.config import MethodType

from dataclasses import dataclass
from typing import Callable


def get_recent_klines(symbol: str, window: int=200):

    bc = Client(*retrieve_keys())

    data = bc.get_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE, "200 minute ago UTC")

    data_columns = ["Time", "Open", "High", "Low", "Close", "Volume", "CloseTime", "QuoteAssetVolume", "NumberOfTrades", "TakerBuyBaseVolume", "TakerBuyQuoteVolume", "NA"]
    klines = pd.DataFrame(data, columns=data_columns)

    klines = klines.drop("NA", axis=1)

    irrelevant_columns = ["CloseTime", "QuoteAssetVolume", "TakerBuyBaseVolume", "TakerBuyQuoteVolume"]
    klines = klines.drop(irrelevant_columns, axis=1)

    klines = klines.astype(float)


@dataclass
class Trade:
    symbol = str
    quote_quantity = float 
    buy_price = float
    stop_price = Callable

    def __post_init__(self):
        
        # TODO remove hardcode
        window = 200

        self.klines = get_recent_klines(self.symbol, window)
        self.socket = 

    def should_buy():
        
        
    def should_sell(): 

    from ta.trend import ema_indicator as EMA


    ema_windows = [20, 50, 100, 200]
    ema_windows


    for window in ema_windows:
        klines[f"EMA{window}"] = EMA(klines.Close, window)
        
    klines.head()



    from ta.volatility import bollinger_hband, bollinger_lband, bollinger_mavg


    klines["BBMid"] = bollinger_mavg(klines.Close, window=20)
    klines["BBHigh"] = bollinger_hband(klines.Close, window=20)
    klines["BBLow"] = bollinger_lband(klines.Close, window=20)

    klines


    from ta.momentum import rsi
    from ta.momentum import stoch


    klines["RSI"] = rsi(klines.Close, window=14)
    klines["Stoch"] = stoch(klines.High, klines.Low, klines.Close, window=14)
    klines