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
    locks: dict, 
    symbol: str, 
    interval: str, 
    paper_flag: bool,
    stop_loss: float):
    
    if (not paper_flag):
        buy_id, sell_quantity = buy_trade(symbol, 15) #buy in
    
    buy_price = current_price_f(symbol)
    print(f"{GREY}BUY PRICE{WHITE}: {buy_price}")
    start_time = time.time()
    print(f"Start: {get_time(start_time-8*3600)} - {start_time}\n")

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
            print(f"{GREY}SELL PRICE{WHITE}: {sell_price}")
            end_time = time.time()
            print(f"End: {get_time(end_time-8*3600)} - {end_time}\n", end='\r')
            print(f"{profit_color}PROFIT{WHITE}: {profit}%\n")
            break
        
        #top value - 'stop_loss' percent of buy in price
        stop_price = max_price - buy_price*stop_loss
        time.sleep(30)
        
    lock_1_flag = False
    lock_2_flag = False
    while True:
        if not lock_1_flag: #if lock 1 task not done yet
            if not locks['current_trades'].locked(): #wait until lock is open
                locks['current_trades'].acquire()
                #remove symbol from current trades
                current_trades.remove(symbol) 
                locks['current_trades'].release()
                lock_1_flag = True #flag is true to mark task is completed
        if not lock_2_flag: #if lock 2 task not done yet
            if not locks['profits_file'].locked(): #wait until lock is open
                locks['profits_file'].acquire()
                #add profit data to profits file (locked to avoid collisions)
                add_row_to_csv(
                    file_path = os.path.join("logs", "profits.csv"), 
                    data = [
                        profit, 
                        buy_in_gain,
                        interval,
                        stop_loss,
                        buy_price, 
                        sell_price, 
                        start_time, 
                        end_time
                    ])
                locks['profits_file'].release()
                lock_2_flag = True  # flag is true to mark task is completed
        if (lock_1_flag and lock_2_flag): #if both locked tasks are done
            break #break to finish trade cycle

    return

#PARAM (none)
#RETURN (none)
def main():
    #Parameters
    global buy_in_gain
    global current_trades #list of all coins currently being traded
    
    buy_in_gain = 10 #gain required in 5 minute period for buy in
    interval = '1m'
    paper_flag = True #if true than using paper money, else using real money
    current_trades = []
    
    locks = { #locks for thread synchronization
        'current_trades': threading.Lock(),
        'profits_file': threading.Lock(),
    }
    
    # MAIN LOOP
    while True:
        try: #try-except incase api requests raise error or loss of connection
        
            #find coins to trade
            top_coins = top_gainers(buy_in_gain)
            max_gain = 1
            
            #TODO: cycle through current_trades and top_coins in multiple 
            # threads to speed up execution time
            
            #TODO: switch to websocket for data source instead of api requests
            
            locks['current_trades'].acquire()
            for coin in current_trades: #if coin already being traded, skip it
                if coin in top_coins:
                    top_coins.drop(coin)
            locks['current_trades'].release()
            
            for coin in top_coins.index:
                init_coin(coin, interval) #if new coin, create file for data
                klines = download_to_csv(coin, interval, 5) #download candles
                
                last_klines = klines.tail(5) #only analyze last 5 candles
                for index in range(1,5):
                    try:
                        if (last_klines.iloc[-index]['c'] < \
                            last_klines.iloc[-index]['o']): 
                            #if bearish candle, skip this index
                            continue
                    except IndexError: #incase coin has less than 5 candles
                        break
                    else:
                        gain = last_klines.iloc[-1]['c']/ \
                            last_klines.iloc[-index]['o']
                        max_gain = max(gain, max_gain)
                        if (gain > (1+buy_in_gain/100)):
                            #notify computer about buying in
                            print(f"{GREY}CRITERIA ACHIEVED{WHITE} buying " +
                                f"into {coin}.")
                            locks['current_trades'].acquire()
                            current_trades.append(coin)
                            locks['current_trades'].release()
                            #creating trade loop thread for coin
                            threading.Thread(
                                target = trade_loop, 
                                args = [
                                    locks, 
                                    coin, 
                                    interval,
                                    paper_flag,
                                    buy_in_gain/100]
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


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{GREY}STATUS {WHITE}Finishing Program...")
        sys.exit()
