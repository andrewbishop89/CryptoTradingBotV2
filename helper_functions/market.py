#!/usr/bin/python3
#
# market.py: contains all the functions involving market information
#
# Andrew Bishop
# 2021/11/13
#

# modules imported
import pandas as pd

from constants.parameters import *
from helper_functions.api import *

#----------------------------------functions-----------------------------------

def daily_ticker_24hr(symbol: str=None) -> pd.DataFrame:
    """
    Description:
        Returns DataFrame of symbol(s) of 24h price data.
    Args:
        symbol (str): symbol of coin to return
    Returns:
        pd.DataFrame: DataFrame of symbol(s) of all 24h price data. 
    """
    if symbol:
        tickers = send_public_request('/api/v3/ticker/24hr', payload={'symbol': symbol})
        df = pd.DataFrame(tickers, index=[0])
    else:
        tickers = send_public_request('/api/v3/ticker/24hr')
        df = pd.DataFrame(tickers)
    df = df[df['symbol'].str.contains('USDT')]
    df = df.set_index('symbol')
    return df

def top_price_gainers(min_percent: float = 0, max_percent: float = 0, limit: int=None) -> pd.DataFrame:
    """
    Description:
        Returns a list of the top gainer currencies in the last 24 hours.
    Args:
        min_percent (float, optional): minimum threshold percent (defaults 
        to 0)
        max_percent (float, optional): maximum threshold percent (defaults 
        to 0)
    Returns:
        pd.DataFrame: all coins that have a daily price change inbetween the 
        min and max percentages
    """
    df = daily_ticker_24hr()
    df = df['priceChangePercent'].astype(float)
    df = df.sort_values()
    
    if min_percent:
        df = df[df > min_percent]
    if max_percent:
        df = df[df < max_percent]
    return df.iloc[-limit:] if (limit and len(df) > limit) else df

def top_volume_gainers(min_volume: float=0, limit: int=None) -> pd.DataFrame:
    """
    Description:
        Returns a list of the top volume gainer currencies in the last 24 
        hours.
    Args:
        amount (int, optional): amount of symbols to return (defaults to 0).
    Returns:
        pd.DataFrame: all coins that have the highest daily volume.
    """
    df = daily_ticker_24hr()
    df = df['volume'].astype(float)
    df = df.sort_values()
    
    if min_volume:
        df = df[df > min_volume]
    return df.iloc[-limit:] if (limit and len(df) > limit) else df

