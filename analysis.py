#!/usr/bin/python3
#
# analysis.py: contains all the functions involving technical analysis or any 
# other mathematical operations and transformations.
#
# Andrew Bishop
# 2021/11/13
#

# modules imported
import pandas as pd
import numpy as np
from ta.trend import ema_indicator
from ta.trend import sma_indicator

from parameters import *


#----------------------------------functions-----------------------------------

def fibonacci_retracement_levels(
    start_price: float, 
    end_price: float) -> list:
    """
    Description:
        Calculates the fibonacci price levels for parameters specified.
    Args:
        start_price (float): start point for fibonacci retracement levels
        end_price (float): end point for fibonacci retracement levels
    Returns:
        list: list of all floats of all fibonacci price levels
    """
    
    level_percentages = np.array([0, 0.382, 0.5, 0.618, 0.764, 0.88, 1, -0.25, 
        -0.618, -1.618])
    price_difference = end_price-start_price
    return [(end_price - (price_difference*percentage)) for percentage in \
        level_percentages]
    

def list_to_series(data: list) -> pd.Series:
    """
    Description:
        Converts a list object to a series object.
    Args:
        data (list): list of data to be converted
    Returns:
        pd.Series: list of data in converted series form
    """
    return pd.Series(np.array(data))


def EMA(data, window: int=50, offset: int=0) -> pd.Series:
    """
    Description:
        Calculates Exponential Moving Average (EMA) of data passed as 
        parameter.
    Args:
        data: list/series of data used in calculation
        window (int, optional): amount of elements in average (defaults to 50)
    Returns:
        list: list of EMA values for all data passed
    """
    return pd.Series(ema_indicator(data, window=window).values)

def SMA(data, window: int=10) -> pd.Series:
    """
    Description:
        Calculates Simple Moving Average (SMA) of data passed as parameter.
    Args:
        data: list/series of data used in calculation
        window (int, optional): amount of elements in average (defaults to 10)
    Returns:
        list: list of SMA values for all data passed
    """
    return pd.Series(sma_indicator(data, window=window).values)


def SMMA(klines: pd.DataFrame, window: int) -> list:
    """
    Description:
        Calculates Smoothed Moving Average (SMMA) of data passed as parameter.
    Args:
        klines (pd.DataFrame): list of data used in calculation
        window (int): amount of elements in average
    Raises:
        IndexError: if data length is smaller than half the calculation window
    Returns:
        list: list of SMMA values for all data passed
    """
    closing_prices = [kline['c'] for kline in klines.iloc]
    if len(klines) < 2*window:
        print(f"{RED}ERROR{WHITE} Window not large enough for SMMA calculation\
            (NEED: {2*window}, RECIEVED: {len(klines)}).")
        raise IndexError
    first_value = SMA(closing_prices, window=window)[-window]
    smma_values = [(first_value*(window-1) + closing_prices[-1])/window]
    for index in range(window-1):
        smma_values.append(
            (smma_values[-1]*(window-1) + closing_prices[index-window])/window)
    return smma_values


#-------------------------------chart-patterns---------------------------------

def bull_flag(klines: pd.DataFrame) -> bool:
    """
    Description:
        Checks whether the last 5 candles follow a bullish flag candle pattern.
    Args:
        klines (pd.DataFrame): The last 5 most recent candles
    Returns:
        bool: true if bull flag was just formed, false otherwise
    """
    
    lows = klines[:, 'l']
    highs = klines[:, 'h']
    close_4 = klines[4, 'c']
    
    criteria_1 = (lows[0] < lows[1]) and (lows[0] < lows[2]) \
        and (lows[0] < lows[3])
    criteria_2 = (highs[1] > highs[2]) and (highs[2] > highs[3])
    criteria_3 = (close_4 > highs[3])
    
    return (criteria_1 and criteria_2 and criteria_3)
