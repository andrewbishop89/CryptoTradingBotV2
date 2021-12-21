#!/usr/bin/python3
#
# method_1.py: contains functions for method 1 of crypto bot version 2.
#
# Andrew Bishop, Ryan Manak
# 2021/11/25
#
# Crontab: 
# @reboot sleep 120 && cd ~/CryptoTradingBotV2 && /Library/Frameworks/
# Python.framework/Versions/3.8/bin/python3 ~/CryptoTradingBotV2/method_1.py 
# >> ~/CryptoTradingBotV2/cron_logs.txt 2>&1
#

# modules imported
import sys
import threading
import pync

from data_collection import *
from market import *
from trade import *
from parameters import *


# functions
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

#TODO: create a different lock for each coin, make a specific thread for data 
# collection of that coin and make it so that multiple trade options can be 
# executed at the same time without collisions (ie; trade with gain 10, 5, 3 
# with different stop losses at same time while only collecting data once)

#TODO: switch to websocket for data source instead of api requests

#TODO: either make crontab write to non plain text file or make it so that 
# print statements to text file don't have any invalid characters in them and 
# fix so that os.get_ternibal_size() is not called if running from crontab

#TODO: cycle through current_trades and top_coins in multiple
# threads to speed up execution time

#TODO: run on a crontab that restarts the program whenever network connection 
# is obtained again, also restart program on computer reboot

#TODO: go through setup.py and add specifications to all functions

#TODO: make function for sleep time for main

#TODO: make function for main string formatting and printing

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
        try:
            klines = download_to_csv(symbol, interval)
            current_price = klines.iloc[-1]['c']
            current_high = klines.iloc[-1]['h']
            
            max_price = max(max_price, current_high)
            
            if (current_price < stop_price): # if below stop loss take losses
                if (not paper_flag):
                    sell_trade(symbol, quantity=sell_quantity)
                sell_price = current_price_f(symbol)
                profit = get_profit(buy_price, sell_price, paper=paper_flag)
                profit_color = GREEN if profit > 0 else RED
                print(f"{profit_color}CRITERIA ACHIEVED{WHITE} selling {symbol}.")
                print(f"{GREY}SELL PRICE{WHITE}: {sell_price}")
                end_time = time.time()
                print(f"End: {get_time(end_time-8*3600)} - {end_time}\n", end='\r')
                print(f"{profit_color}PROFIT{WHITE}: {profit}%\n")
                break
            
            #top value - 'stop_loss' percent of buy in price
            stop_price = max_price - buy_price*stop_loss
            time.sleep(30)
            
        #incase loss of network during trade
        except (requests.ConnectionError, requests.Timeout) as exception:
            lost_connection_sleep(60) #sleep for 60 seconds
        
    lock_1_flag = False
    lock_2_flag = False
    while True:
        if not lock_1_flag: #if lock 1 task not done yet
            if not locks['current_trades'].locked(): #wait until lock is open
                #lock and remove symbol from current trades
                locks['current_trades'].acquire()
                current_trades.remove(symbol) 
                locks['current_trades'].release()
                lock_1_flag = True #flag is true to mark task is completed
        if not lock_2_flag: #if lock 2 task not done yet
            if not locks['profits_file'].locked(): #wait until lock is open
                #lock and add profit data to profits file 
                locks['profits_file'].acquire()
                add_row_to_csv(
                    file_path = os.path.join("logs", "profits.csv"), 
                    data = [
                        profit,
                        symbol,
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
def run_method(buy_in_gain_param: float):
    #Parameters
    global buy_in_gain
    global current_trades
    
    buy_in_gain = buy_in_gain_param  #gain required in 5 minute period for buy in
    interval = '1m' #candle interval used in analysis
    paper_flag = True #if true than using paper money, else using real money
    current_trades = [] #list of symbols that are currently being traded
    terminal_width = os.get_terminal_size().columns #width of terminal window
    
    locks = { #locks for thread synchronization
        'current_trades': threading.Lock(),
        'profits_file': threading.Lock(),
    }
    
    print(f"{GREY}STARTING PROGRAM{WHITE}\nBuy-in Gain: {buy_in_gain}%\n" + 
          f"Paper: {paper_flag}\n")
    
    # MAIN LOOP
    while True:
        try: #try-except for handling loss of internet connection
        
            #find coins to trade
            top_coins = top_gainers(buy_in_gain)
            max_gain = 1
            
            #copying list to prevent collisions
            locks['current_trades'].acquire() 
            current_trades_copy = current_trades.copy()
            locks['current_trades'].release()
            
            #if coin already being traded, skip it
            for coin in current_trades_copy:
                if coin in top_coins:
                    top_coins.drop(coin)
            del current_trades_copy
            
            for coin in top_coins.index:
                init_coin(coin, interval) #if new coin, create file for data
                klines = download_to_csv(coin, interval, 5) #download candles
                
                last_klines = klines.tail(5) #only analyze last 5 candles
                for index in range(1,5):
                    try:
                        #if bearish candle, skip this index
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
                            print(f"{GREY}CRITERIA ACHIEVED{WHITE} buying " +
                                f"into {coin}.")
                            #add coin to current trades
                            locks['current_trades'].acquire()
                            current_trades.append(coin)
                            locks['current_trades'].release()
                            #creating trade loop thread for coin
                            start_trade(
                                thread=threading.Thread(
                                    target=trade_loop,
                                    args=[
                                        locks,
                                        coin,
                                        interval,
                                        paper_flag,
                                        buy_in_gain/100]),
                                symbol=coin)
                            
                            break
            
            #print current program status (statistics)
            current_string = format_string_padding(
                f"Number of Coins: {len(top_coins)}",
                terminal_width=terminal_width)
            current_string += format_string_padding(
                f" Last Max Gain: {round(max_gain*100-100,2)}%",
                terminal_width=terminal_width)
            current_string += format_string_padding(
                f" Thread Count: {threading.active_count()}",
                terminal_width=terminal_width)
            #subtract 8*3600 to convert from UTC to GMT-8 time
            current_string += format_string_padding(
                f" Time: {get_time(time.time()-8*3600)}",
                terminal_width=terminal_width)
            print(current_string)

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
        except (requests.ConnectionError, requests.Timeout) as exception:
            lost_connection_sleep(300, terminal_width=terminal_width)


if __name__ == '__main__': #only run main() when running this file as main
    
    pync.notify(f"Buy-In Gain: {buy_in_gain}%", title="Starting CryptoBotV2")
    threading.current_thread().name = "Thread-MAIN"
    
    try:
        run_method(buy_in_gain_param=10)
    except KeyboardInterrupt:
        print(f"\n{GREY}STATUS {WHITE}Finishing Program. Thread Count: " + 
              f"{threading.active_count()}")
        sys.exit()
    finally:
        pync.notify("Finishing CrytoBotV2", title="The program is " + 
                    "terminating.")
