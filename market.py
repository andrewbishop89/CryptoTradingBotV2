#!/usr/bin/python3
#
# market.py: contains all the functions involving market information
#
# Andrew Bishop
# 2021/11/13
#

# modules imported
import pandas as pd

from parameters import *
from api import *


# functions
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

#PARAM min_percent(float) = 0: minimum threshold percent
#PARAM max_percent(float) = 0: maximum threshold percent
#RETURN (DataFrame): all coins that have a daily price change inbetween min 
# and max percentages
def top_gainers(min_percent: float = 0, max_percent: float = 0):
    price_change = send_public_request('/api/v3/ticker/24hr')
    df = pd.DataFrame.from_dict(price_change)
    df = df[df['symbol'].str.contains(
        'USDT')]
    #df = df[df['symbol'].str.contains('DOWN') == False]
    #df = df[df['symbol'].str.contains('UP') == False]
    df = df.reset_index().set_index('symbol')
    if min_percent:
        df = df[df['priceChangePercent'].astype(float) > min_percent]
    if max_percent:
        df = df[df['priceChangePercent'].astype(float) < max_percent]
    df = df['priceChangePercent'].astype(float)
    df = df.sort_values()
    return df
