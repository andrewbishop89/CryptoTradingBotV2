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
