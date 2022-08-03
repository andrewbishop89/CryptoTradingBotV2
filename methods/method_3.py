#!/usr/bin/python3
#
# .py: 
#
# Andrew Bishop
# 2022/07/10
#

from helper_functions import analysis


def buy_conditions(klines) -> bool:
        
    currnet_price = klines["5m"].loc[-1, "c"]
        
    ema_21 = analysis.EMA(klines["5m"], 21)[-1]
    ema_50 = analysis.EMA(klines["5m"], 50)[-1]
    ema_100 = analysis.EMA(klines["5m"], 100)[-1]
    
    return (ema_21 > ema_50) and (ema_50 > ema_100) 

    
def sell_conditions(klines) -> bool:
    
    currnet_price = klines["5m"].loc[-1, "c"]

    #TODO include risk multiplier, buy price and other sell conditions in here
    
    return