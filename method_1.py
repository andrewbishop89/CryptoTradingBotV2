#!/usr/bin/python3
#
# method_1.py: contains functions for method 1 of crypto bot version 2.
#
# Andrew Bishop, Ryan Manak
# 2021/11/25
#

# modules imported
import sys
import pync
import threading

from data_collection import *
from graphing import graph
from market import *
from trade import *
from parameters import *


# functions
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

#PARAM lock(threading.Lock): lock for making changes to current trades list
#PARAM symbol(str): symbol of currency to trade
#PARAM interval(str): interval of klines to be used for analysis
#PARAM paper_flag(bool): to indicate whether to use real or paper money
#RETURN (none)
def trade_loop(
    lock: threading.Lock, 
    symbol: str, 
    interval: str, 
    paper_flag: bool):
    
    if (not paper_flag):
        buy_id, sell_quantity = buy_trade(symbol, 15) #buy in
    
    stop_loss = 0.1 #stop loss percent
    
    buy_price = current_price_f(symbol)
    print(f"{GREY}BUY PRICE{WHITE}: {buy_price}")
    print(f"Start: {get_time(time.time()-8*3600)} - {time.time()}\n")

    max_price = buy_price
    stop_price = buy_price*(1-stop_loss)
    
    while True:
        klines = download_to_csv(symbol, interval)
        current_price = klines.iloc[-1]['c']
        current_high = klines.iloc[-1]['h']
        
        max_price = max(max_price, current_high)
        
        if (current_price < stop_price): # if below stop loss take losses
            if (not paper_flag):
                sell_trade(symbol, quantity=sell_quantity)
            sell_price = current_price_f(symbol)
            profit = round((sell_price/buy_price-1)*100, 2)
            profit_color = GREEN if profit > 0 else RED
            print(f"{BLUE}CRITERIA ACHIEVED{WHITE} selling {symbol}.")
            print(f"End: {get_time(time.time()-8*3600)} - {time.time()}\n", end='\r')
            print(f"{profit_color}PROFIT{WHITE}: {profit}%\n")
            break
        
        #top value - 'stop_loss' percent of buy in price
        stop_price = max_price - buy_price*stop_loss
        time.sleep(30)
        
    lock.acquire()
    current_trades.remove(symbol)
    lock.release()
        
    return

#PARAM (none)
#RETURN (none)
def main():
    #Parameters
    buy_in_gain = 10 #gain required in 5min period for buy in
    interval = '1m'
    paper_flag = True #if true than using paper money, else using real money
    
    lock = threading.Lock() #for thread synchronization
    global current_trades #list of all coins currently being traded
    current_trades = []
    
    # MAIN LOOP
    while True:
        try: #try-except incase api requests raise error or loss of connection
        
            #find coins to trade
            top_coins = top_gainers(buy_in_gain)
            max_gain = 1
            
            #TODO: cycle through current_trades and top_coins in multiple 
            # threads to speed up execution time
            
            lock.acquire()
            for coin in current_trades: #if coin already being traded, skip it
                if coin in top_coins:
                    top_coins.drop(coin)
            lock.release()
            
            for coin in top_coins.index:
                init_coin(coin, interval) #if new coin, create file for data
                klines = download_to_csv(coin, interval, 5) #download recent data
                
                last_klines = klines.tail(5) #only analyze last 5 candles
                for index in range(1,5):
                    try:
                        if (last_klines.iloc[-index]['c'] < \
                            last_klines.iloc[-index]['o']):
                            continue
                    except IndexError: #incase coin has less than 5 candles
                        break
                    else:
                        gain = last_klines.iloc[-1]['c']/ \
                            last_klines.iloc[-index]['o']
                        max_gain = max(gain, max_gain)
                        if (gain > (1+buy_in_gain/100)):
                            #notify computer about buying in
                            #pync.notify(f"{coin}: {round(gain*100-100,2)}%", 
                            #    title="CTB2")
                            print(f"{GREY}CRITERIA ACHIEVED{WHITE} buying " +
                                f"into {coin}.")
                            lock.acquire()
                            current_trades.append(coin)
                            lock.release()
                            #creating trade loop thread for coin
                            threading.Thread(
                                target = trade_loop, 
                                args = [lock, 
                                        coin, 
                                        interval,
                                        paper_flag]
                                ).start()
                            break
            
            
            #print current program status (statistics)
            current_string = format_string_padding(
                f" Number of Coins: {len(top_coins)}")
            current_string += format_string_padding(
                f" Last Max Gain: {round(max_gain*100-100,2)}%")
            current_string += format_string_padding(
                f" Thread Count: {threading.active_count()}")
            #subtract 8*3600 to convert from UTC to GMT-8 time
            current_string += format_string_padding(
                f" Time: {get_time(time.time()-8*3600)}")
            print(current_string, end='\r')

            
            #change sleep time depending on last measure max gain
            if (max_gain > buy_in_gain*0.9):
                time.sleep(30)
            elif (max_gain > buy_in_gain*0.7):
                time.sleep(60)
            elif (max_gain > buy_in_gain*0.5):
                time.sleep(90)
            elif (max_gain > buy_in_gain*0.3):
                time.sleep(120)
            else:
                time.sleep(240)
            
        #incase a network connection error is raised
        except requests.exceptions.ReadTimeout:
            print(f"{RED}ERROR {WHITE} ReadTimeout Error Raised. Sleeping " +
                "for 5 minutes.")
            time.sleep(300)

try:
    main()
except KeyboardInterrupt:
    print(f"\n{GREY}STATUS {WHITE}Finishing Program...")
    sys.exit()
