#!/usr/bin/python3
#
# analysis.py: contains all the functions involving technical analysis or any 
# other mathematical operations and transformations.
#
# Andrew Bishop, Ryan Manak
# 2021/11/13
#

# modules imported
import pandas as pd
import numpy as np
from ta.trend import sma_indicator

from parameters import *


# functions
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

# indicators
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

#PARAM start_price(float): start point for fibonacci retracement levels
#PARAM end_price(float): end point for fibonacci retracement levels
#RETURN fibonacci_levels(list[floats]): list of all fibonacci price levels
def fibonacci_retracement_levels(
    start_price: float, 
    end_price: float):
    
    level_percentages = np.array([0, 0.382, 0.5, 0.618, 0.764, 0.88, 1, -0.25, 
        -0.618, -1.618])
    price_difference = end_price-start_price
    return [(end_price - (price_difference*percentage)) for percentage in \
        level_percentages]
    

def list_to_series(data):
    return pd.Series(np.array(data))

#PARAM data(): TODO
#PARAM window(): TODO
#RETURN (): TODO 
def SMA(data, window=10):
    series = list_to_series(data)
    sma_values = sma_indicator(series, window=window).values.tolist()
    return sma_values

#PARAM klines(DataFrame): candles to analyze
#PARAM window(int): number of values for SMMA
#RETURN (DataFrame): 
def SMMA(klines: pd.DataFrame, window: int):
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

#PARAM klines(DataFrame): candles to analyze
#PARAM short_window
"""
def triple_SMMA_check(
    klines: pd.DataFrame, 
    short_window: int, 
    mid_window: int, 
    long_window: int):
    
    short_smma = SMMA(klines.iloc[-2*short_window:], short_window)
    mid_smma = SMMA(klines.iloc[-2*mid_window:], mid_window)
    long_smma = SMMA(klines.iloc[-2*long_window:], long_window)
    return (short_smma[-1] > mid_smma[-1]) and (mid_smma[-1] > long_smma[-1]) and \
        (trend_direction({}, data=short_smma, window=5) == 'up') and \
        (trend_direction({}, data=mid_smma, window=5) == 'up') and \
        (trend_direction({}, data=long_smma, window=5) == 'up')
"""

# chart patterns
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

#PARAM klines(DataFrame): 5 candles in a row
#RETURN (bool): true if bull flag was just formed, false otherwise
#DESCRIPTION: 5 candles, low_0 < lows_1,2,3 and high_1 > high_2 > high_3 and 
# then close_4 > high_3
def bull_flag(klines: pd.DataFrame):
    lows = klines[:, 'l']
    highs = klines[:, 'h']
    close_4 = klines[4, 'c']
    
    criteria_1 = (lows[0] < lows[1]) and (lows[0] < lows[2]) \
        and (lows[0] < lows[3])
    criteria_2 = (highs[1] > highs[2]) and (highs[2] > highs[3])
    criteria_3 = (close_4 > highs[3])
    
    return (criteria_1 and criteria_2 and criteria_3)
