#!/usr/bin/python3
#
# analysis.py: contains all the functions involving technical analysis or any 
# other mathematical operations and transformations.
#
# Andrew Bishop, Ryan Manak
# 2021/11/13
#

# modules imported
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